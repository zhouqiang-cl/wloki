#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import cdecimal

# add gevent monkey patch
from gevent.monkey import patch_all
patch_all()

sys.modules["decimal"] = cdecimal
import gevent.event

import site

# Add loki/site-packages to sys.path
# as if it is a standard site-packages directory
site.addsitedir('site-packages')

_unpatch_async_result = gevent.event.AsyncResult


class _AsyncResult(gevent.event.AsyncResult):
    def set_exception(self, exception, exc_info=None):
        if exception is not None and exc_info is None:
            exc_info = sys.exc_info()

        if exc_info == (None, None, None):
            exc_info = None

        _unpatch_async_result.set_exception(self, exception, exc_info)

# monkey patch gevent.event.AsyncResult
gevent.event.AsyncResult = _AsyncResult


from .utils import load_privilege_definitions

load_privilege_definitions(__file__)
