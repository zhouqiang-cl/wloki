# -*- coding: utf-8 -*-

# Claim absolute import to prevent `import gevent` to import utils.gevent
from __future__ import absolute_import
import collections
import copy
import sys
import os
import logging
import datetime
import cProfile
import tempfile
import pstats
from functools import wraps
from math import factorial

import simplejson

from torext import current_app


# For backward compatibility
from .gevent import asyncrequest  # NOQA


def list_flat(l):
    for subitem in l:
        if isinstance(subitem, collections.Iterable) and not isinstance(subitem, basestring):
            for item in list_flat(subitem):
                yield item
        else:
            yield subitem


def profile(sort='cumulative', lines=50, strip_dirs=False):
    """A decorator which profiles a callable.
    Example usage:

    >>> @profile
        def factorial(n):
            n = abs(int(n))
            if n < 1:
                    n = 1
            x = 1
            for i in range(1, n + 1):
                    x = i * x
            return x
    ...
    >>> factorial(5)
    Thu Jul 15 20:58:21 2010    /tmp/tmpIDejr5

             4 function calls in 0.000 CPU seconds

       Ordered by: internal time, call count

       ncalls  tottime  percall  cumtime  percall filename:lineno(function)
            1    0.000    0.000    0.000    0.000 profiler.py:120(factorial)
            1    0.000    0.000    0.000    0.000 {range}
            1    0.000    0.000    0.000    0.000 {abs}

    120
    >>>
    """
    def outer(fun):
        def inner(*args, **kwargs):
            file = tempfile.NamedTemporaryFile()
            prof = cProfile.Profile()
            try:
                ret = prof.runcall(fun, *args, **kwargs)
            except:
                file.close()
                raise

            prof.dump_stats(file.name)
            stats = pstats.Stats(file.name)
            if strip_dirs:
                stats.strip_dirs()
            if isinstance(sort, (tuple, list)):
                stats.sort_stats(*sort)
            else:
                stats.sort_stats(sort)
            stats.print_stats(lines)

            file.close()
            return ret
        return inner

    # in case this is defined as "@profile" instead of "@profile()"
    if hasattr(sort, '__call__'):
        fun = sort
        sort = 'cumulative'
        outer = outer(fun)
    return outer


def catch_exception(logger=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                fn(*args, **kwargs)
            except Exception as e:
                if logger:
                    logger.exception(str(e))
                capture_exception()
        return wrapper
    return decorator


def capture_exception(*args, **kwargs):
    from ..app import sentry_client

    if 'exc_info' not in kwargs:
        kwargs['exc_info'] = sys.exc_info()

    if current_app.settings.get('DEBUG', True):
        exc_info = kwargs['exc_info']
        if exc_info is None:
            exc_info = sys.exc_info()
        logging.warn('[DEBUG SKIP SENTRY] capture exception: %s', exc_info)
    else:
        sentry_client.captureException(*args, **kwargs)


def _handle_object_for_json(obj):
    if isinstance(obj, datetime.datetime):
        return str(obj)


def encode_json(data):
    return simplejson.dumps(data,
                            ensure_ascii=False,
                            default=_handle_object_for_json,
                            for_json=True)


def utf8(string):
    ''' transter string to utf8
    '''
    if isinstance(string, unicode):
        return string.encode('utf-8')
    return string


def _to_float3(n):
    return float('%.3f' % n)


def _3left(n):
    s = str(n)
    if '.' in s:
        pre, suf = s.split('.')
        s = '.'.join([pre, suf[:3]])
    return _to_float3(float(s))


def merge_dict(base, other):
    assert isinstance(base, collections.MutableMapping)
    assert isinstance(other, collections.MutableMapping)
    base = copy.copy(base)
    for k, v in other.iteritems():
        if k in base \
                and isinstance(base[k], collections.MutableMapping) \
                and isinstance(v, collections.MutableMapping) \
                and v:
            base[k] = merge_dict(base[k], v)
        elif v:
            base[k] = copy.copy(v)
    return base


def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in xrange(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level\
                package")
    return "%s.%s" % (package[:dot], name)


def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]


def load_privilege_definitions(filepath):
    dirname = os.path.dirname(filepath)
    pfilename = 'privileges.py'
    print 'Loading privilege modules:',
    for i in os.listdir(dirname):
        _dirpath = os.path.join(dirname, i)
        if not os.path.isdir(_dirpath):
            continue

        pfilepath = os.path.join(_dirpath, pfilename)
        if os.path.exists(pfilepath):
            module_name = 'loki.%s.privileges' % i
            import_module(module_name)
            print module_name,
    print '| Done.'
