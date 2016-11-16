#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps
from collections import namedtuple
from loki import errors
from loki.privilege.models import authorize


HandlerContext = namedtuple('HandlerContext', ('handler', 'args', 'kwargs'))


def require_node_privileges(privilege, _get_node_id=None):
    def decorator(method):
        @wraps(method)
        def wrapper(handler, *args, **kwargs):
            if not handler.user:
                raise errors.AuthenticationNotPass('Must login to access this url')


            context = HandlerContext(handler, args, kwargs)
            if _get_node_id:
                get_node_id = _get_node_id
            else:
                get_node_id = lambda c: int(c.handler.get_argument('node_id'))
            node_id = get_node_id(context)

            authorize(privilege, handler.user.username, node_id=node_id)
            return method(handler, *args, **kwargs)
        return wrapper
    return decorator
