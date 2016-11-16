#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import sys
import logging
import traceback
import gevent
from gevent.hub import Hub
from gevent.event import AsyncResult
from werkzeug._reloader import StatReloaderLoop
from raven.transport.gevent import GeventedHTTPTransport
from requests import Session
from requests.adapters import HTTPAdapter

from ..errors import SentryRequestFailed


# Requests init
_session = Session()
_adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=1)
_session.mount('http://', _adapter)


IGNORE_ERROR = Hub.SYSTEM_ERROR + Hub.NOT_ERROR


def register_hub_error_handler(error_handler):
    assert not hasattr(Hub, '_origin_handle_error'),\
        'This function should not be called twice'

    Hub._origin_handle_error = Hub.handle_error

    def custom_handle_error(self, context, type, value, tb):
        if not issubclass(type, IGNORE_ERROR):
            # print 'Got error from greenlet:', context, type, value, tb
            error_handler(context, (type, value, tb))

        self._origin_handle_error(context, type, value, tb)

    Hub.handle_error = custom_handle_error

    return error_handler


class GeventReloaderLoop(StatReloaderLoop):
    name = 'gevent_stat'

    _sleep = staticmethod(gevent.sleep)

    @classmethod
    def run_with_reloader(cls, main_func, extra_files=None, interval=1,
                          reloader_type='auto'):
        """Run the given function in an independent python interpreter."""
        import signal

        reloader = cls(extra_files, interval)
        signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))

        try:
            if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
                gevent.spawn(reloader.run)
                main_func()
            else:
                sys.exit(reloader.restart_with_reloader())
        except KeyboardInterrupt:
            sys.exit(0)


def asyncrequest(method, url, timeout=None, **kwargs):
    def send_request(method, url, **kwargs):
        try:
            req = _session.request(method, url, **kwargs)
        except Exception, e:
            result.set_exception(e)
        else:
            result.set(req)
    result = AsyncResult()
    logging.info('asyncrequest: %s', url)
    gevent.spawn(send_request, method, url, **kwargs)
    ret = result.get(timeout=timeout)
    return ret


class CustomGeventHTTPTransport(GeventedHTTPTransport):
    def async_send(self, data, headers, success_cb, failure_cb):
        """
        Spawn an async request to a remote webserver.
        """
        # this can be optimized by making a custom self.send that does not
        # read the response since we don't use it.
        self._lock.acquire()
        g = gevent.spawn(
            self.__send, data, headers
        )
        g.link(lambda x: self._done(x, success_cb, failure_cb))
        return g

    def __send(self, *args, **kwargs):
        try:
            return super(CustomGeventHTTPTransport, self).send(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            raise SentryRequestFailed(str(e))
