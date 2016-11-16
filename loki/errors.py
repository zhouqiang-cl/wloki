#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torext.errors import (  # NOQA
    ParamsInvalidError, ValidationError,
    AuthenticationNotPass, OperationNotAllowed,
    DoesNotExist
)
from tornado.web import HTTPError  # NOQA


class LokiBaseError(Exception):
    """Base class for loki custom exceptions"""


class HasNoPermission(LokiBaseError):
    pass


class RequestError(LokiBaseError):
    pass


class FatalError(LokiBaseError):
    pass


class TemporaryServerError(LokiBaseError):
    pass


class MailQueueFullError(LokiBaseError):
    pass


class SentryRequestFailed(LokiBaseError):
    """Raised when raven tried to send a request to sentry but failed whatever reason"""


class MailUnicodeDecodeError(UnicodeDecodeError):
    def __init__(self, obj, *args):
        self.obj = obj
        UnicodeDecodeError.__init__(self, *args)

    def __str__(self):
        original = UnicodeDecodeError.__str__(self)
        return '%s. You passed in %r (%s)' % (original, self.obj, type(self.obj))
