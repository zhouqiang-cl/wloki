#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from lazy_object_proxy import Proxy
from gevent.lock import RLock


class LazyInit(object):
    func_results = {}
    _lock = None

    def __init__(self, with_lock):
        if with_lock:
            self._lock = RLock()

    def __call__(self, func, *args, **kwargs):
        def wrapper():
            if self._lock is not None:
                with self._lock:
                    return self._get_func_result(func, *args, **kwargs)
            else:
                return self._get_func_result(func, *args, **kwargs)

        assert callable(func), "lazy_init must be called with callable object"
        if not hasattr(func, "__name__"):
            func.__name__ = "unknown_function"
        return Proxy(wrapper)

    def _get_func_result(self, func, *args, **kwargs):
        func_id = tuple([id(func), func.__name__]) + args + tuple(kwargs.itervalues())
        if not self.func_results.get(func_id, None):
            self.func_results[func_id] = func(*args, **kwargs)
        return self.func_results[func_id]

lazy_init = LazyInit(with_lock=False)
lazy_init_with_lock = LazyInit(with_lock=True)
