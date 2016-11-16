#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import functools
import sys

from tornado.web import HTTPError
from tornado.escape import xhtml_escape
from raven.contrib.tornado import SentryMixin

from torext.handlers import BaseHandler as _BaseHandler
from poseidon.providers.common import ProviderError as CDNProviderError

from ..db import db
from ..app import settings
from .. import errors
from ..user.models import User
from ..utils import capture_exception
from ..utils.cipher import decrypt_token


def is_list(o):
    return isinstance(o, list)


class BaseHandler(_BaseHandler, SentryMixin):
    PREPARES = ['auth']

    require_auth = True

    EXCEPTION_HANDLERS = {
        errors.HTTPError: '_handle_httperror',
        # (errors.ParamsInvalidError,
        #  errors.ValidationError): '_handle_params_invalid_error',
        errors.AuthenticationNotPass: '_handle_auth_not_pass',
        (errors.OperationNotAllowed,
         errors.HasNoPermission):
            '_handle_not_allowed_error',
        CDNProviderError: '_handle_cdn_provider_error'
    }

    def render(self, template_name, **kwargs):
        """Override this method to add global template functions
        """
        # Static file url generator
        kwargs['static'] = self.static_url
        kwargs['user'] = self.user
        kwargs['is_list'] = is_list
        kwargs['settings'] = settings

        # Current path
        import urlparse

        kwargs['url_path'] = urlparse.urlparse(self.request.uri).path

        super(BaseHandler, self).render(template_name, **kwargs)

    def create_token(self, user):
        v = str(user['id'])
        return self.create_signed_value(settings['AUTH_COOKIE'], v)

    def authenticate(self):
        """
        Authenticate user by token, and add user as attribute to self
        """
        self.user = None
        logger = logging.getLogger('loki.user')

        token = self.get_cookie(settings['AUTH_COOKIE'], None)
        token_value = None
        if token:
            token_value = self.decode_signed_value(settings['AUTH_COOKIE'], token)
        else:
            # Try get token from headers
            try:
                token = self.request.headers.get_list(settings['AUTH_TOKEN_HEADER'])[0]
            except (IndexError, TypeError):
                pass
            else:
                if decrypt_token(token, settings['AUTH_TOKEN_PREFIX']):
                    print 'token decrypt', token
                    token_value = token

        if not token_value:
            logger.debug('User token missing')
            return

        try:
            user = User.get(token_value)
        # except User.DoesNotExist:
        except Exception as e:
            logger.debug('User not found by token: %s' % e)
            return

        logger.info('USER: %s go in' % user.username)
        self.user = user

    def prepare_auth(self):
        self.authenticate()

        if self.require_auth:
            if not self.user:
                raise errors.AuthenticationNotPass('Could not authenticate the user')

    def write_data(self, data, status_code=200):
        if data is None:
            self.set_status(204)
            return

        rv = {
            'data': data
        }
        self.set_status(status_code)
        self.write_json(rv)

    def send_error(self, status_code=500, **kwargs):
        """Override implementation to report all exceptions to sentry, even
        after self.flush() or self.finish() is called, for pre-v3.1 Tornado.
        """
        rv = super(BaseHandler, self).send_error(status_code, **kwargs)

        if 500 <= status_code <= 599:
            capture_exception(exc_info=kwargs.get('exc_info'))
        return rv

    def on_finish(self):
        db.session.remove()

    def _handle_httperror(self, e):
        self.set_status(e.status_code)
        self.render('error.html',
                    status_code=e.status_code, message=xhtml_escape(str(e)))

    def _handle_auth_not_pass(self, e):
        self.redirect('/users/login?redirect=' + self.request.uri)

    def _handle_not_allowed_error(self, e):
        self.set_status(403)
        self.render('error.html',
                    status_code=403, message=xhtml_escape(unicode(e)))

    def _handle_params_invalid_error(self, e):
        self.set_status(400)
        self.render('error.html',
                    status_code=400, message=xhtml_escape(unicode(e)))

    def _handle_cdn_provider_error(self, e):
        self.set_status(504)
        self.render('error.html',
                    status_code=500, message=xhtml_escape(unicode(e)))


# TODO Replace all BaseHandler mis uses
class WebHandler(BaseHandler):
    pass


class APIHandler(BaseHandler):
    PREPARES = ['auth']
    require_auth = False

    EXCEPTION_HANDLERS = {
        HTTPError: '_handle_httperror',
        (errors.ParamsInvalidError, errors.ValidationError):
            '_handle_params_invalid_error',
        errors.AuthenticationNotPass: '_handle_auth_not_pass',
        (errors.OperationNotAllowed,
         errors.HasNoPermission):
            '_handle_not_allowed_error',
        errors.DoesNotExist: '_handle_not_exist',
        errors.RequestError: '_handle_request_error',
        errors.FatalError: '_handle_fatal_error',
        errors.TemporaryServerError: '_handle_temporary_server_error',
    }

    def _handle_httperror(self, e):
        self.api_error(e.status_code, str(e))

    def _handle_params_invalid_error(self, e):
        if isinstance(e, errors.ValidationError):
            param_error = e
        else:
            param_error = e.errors[0]

        if isinstance(param_error, tuple):
            param_error = '"%s": %s' % param_error
        elif isinstance(param_error, Exception):
            param_error = unicode(param_error)

        if isinstance(param_error, str):
            param_error = param_error.decode("utf8")

        message = u'Parameter error: %s' % param_error

        self.api_error(400, message)

    def _handle_not_allowed_error(self, e):
        self.api_error(401, str(e))

    def _handle_auth_not_pass(self, e):
        self.api_error(401, str(e))

    def _handle_not_exist(self, e):
        self.api_error(404, str(e))

    def _handle_request_error(self, e):
        self.api_error(504, str(e))

    def _handle_fatal_error(self, e):
        capture_exception(exc_info=sys.exc_info())
        self.api_error(500, str(e))

    def _handle_temporary_server_error(self, e):
        capture_exception(exc_info=sys.exc_info())
        self.api_error(503, str(e))

    def api_error(self, status_code, message, code=None):
        rv = {
            'error': {
                'message': message,
                'code': code
            }
        }
        self.set_status(status_code)
        self.write_json(rv)


def admin_only(method):
    @functools.wraps(method)
    def wrapper(handler, *args, **kwargs):
        if not handler.user:
            raise errors.AuthenticationNotPass('Must login to access this url')
        if handler.user.username not in settings['ADMIN_USERS']:
            raise errors.HasNoPermission('You have no access to this API')
        return method(handler, *args, **kwargs)

    return wrapper
