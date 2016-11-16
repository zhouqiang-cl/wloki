#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from torext import params

from ..app import settings
from .. import wdjsso
from ..base.handlers import BaseHandler


def get_cookie_domain(host):
    if host.startswith('localhost') or host.startswith('127.0.0.1'):
        return None
    if ':' in host:
        return host.split(':')[0]


class LoginParams(params.ParamSet):
    username = params.RegexField(pattern=r'^[\w\.]+$', required=True)
    password = params.Field(length=(6, 0), required=True, null=False)
    redirect = params.Field()


class SSOValidationFailed(Exception):
    pass


class LoginHandler(BaseHandler):
    require_auth = False

    def get(self):
        uri = self.get_argument('redirect', '/')

        if settings['DEBUG']:
            user = {
                'id': settings['DEBUG_USER']
            }
            logging.info('(DEBUG Mode) USER: DEBUG_USER go in')
            self.login(user)
            self.redirect(uri)
            return

        try:
            sso_token = self.get_cookie('sso_session_id')
            if not sso_token:
                raise SSOValidationFailed('No sso token')
            raw_user = wdjsso.get_user_by_sessionid(sso_token)
            if not raw_user:
                raise SSOValidationFailed('No user')
        except SSOValidationFailed as e:
            logging.info("sso validation failed: %s" % e)
            dest_url = 'http://%s/users/login?redirect=%s' %\
                (self.request.host, uri)
            redirect_url = wdjsso.get_login_address(dest_url)
            self.redirect(redirect_url)
            return

        user = self.json_decode(raw_user)

        self.login(user)
        self.redirect(uri)

    def login(self, user):
        token = self.create_token(user)

        self.set_cookie(settings['AUTH_COOKIE'], token,
                        expires_days=settings['COOKIE_EXPIRE_DAY'],
                        domain=get_cookie_domain(self.request.host))


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie(
            settings['AUTH_COOKIE'],
            domain=get_cookie_domain(self.request.host))
        self.redirect('/')


handlers = [
    ('/login', LoginHandler),
    # ('/logout', LogoutHandler),
]
