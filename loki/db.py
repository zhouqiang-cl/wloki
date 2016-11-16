# -*- coding: utf-8 -*-

"""
This module defines mysql and redis connection instances.
"""

from __future__ import absolute_import

import logging
import time

import gevent
from redis import Redis
from redis import ConnectionPool
from redis.connection import Connection
from sqlalchemy import event
from sqlalchemy.engine import Engine

from torext.sql import SQLAlchemy
from .app import settings

sqlalchemy_config = dict(settings.SQLALCHEMY)
sqlalchemy_cdn_system_config = dict(settings.SQLALCHEMY_CDN_SYSTEM)
sqlalchemy_config.setdefault("pool_recycle", 3600)
sqlalchemy_cdn_system_config.setdefault("pool_recycle", 3600)

db = SQLAlchemy(config=sqlalchemy_config, session_options={
    "scopefunc": gevent.getcurrent
})
db_cdn_system = SQLAlchemy(config=sqlalchemy_cdn_system_config, session_options={
    "scopefunc": gevent.getcurrent
})

if settings.SQLDEBUG:
    logging.basicConfig()
    logger = logging.getLogger("sqltime")
    logger.setLevel(logging.DEBUG)

    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement,
                              parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
        logger.debug("Start Query: %s" % statement)

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement,
                             parameters, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop(-1)
        logger.debug("Query Complete!")
        logger.debug("Total Time: %f" % total)

redis_pool_map = {}


def get_redis(host=settings.REDIS_ADDR, port=settings.REDIS_PORT, db=0):
    pool = redis_pool_map.get((host, port, db))
    if pool is None:
        pool = ConnectionPool(connection_class=GeventConnection,
                              host=host,
                              port=port,
                              db=db)
        redis_pool_map[(host, port, db)] = pool
    redis = Redis(connection_pool=pool)
    return redis


class GeventConnection(Connection):
    def _connect(self):
        from gevent import socket
        err = None
        for res in socket.getaddrinfo(self.host, self.port, 0,
                                      socket.SOCK_STREAM):
            family, socktype, proto, canonname, socket_address = res
            sock = None
            try:
                sock = socket.socket(family, socktype, proto)
                # TCP_NODELAY
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                # TCP_KEEPALIVE
                if self.socket_keepalive:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    for k, v in self.socket_keepalive_options.iteritems():
                        sock.setsockopt(socket.SOL_TCP, k, v)

                # set the socket_connect_timeout before we connect
                sock.settimeout(self.socket_connect_timeout)

                # connect
                sock.connect(socket_address)

                # set the socket_timeout now that we're connected
                sock.settimeout(self.socket_timeout)
                return sock

            except socket.error as _:
                err = _
                if sock is not None:
                    sock.close()

        if err is not None:
            raise err
        raise socket.error("socket.getaddrinfo returned an empty list")
