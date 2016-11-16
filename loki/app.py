#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from raven import Client
from gevent.pool import Pool
from gevent import local

from torext.app import TorextApp
from loki import settings as _settings
from loki.mail import Mail
from loki.utils.gevent import CustomGeventHTTPTransport

app = TorextApp(_settings)

settings = app.settings  # NOQA

mail = Mail(app)

greenlet_pool = Pool(settings.GREENLET_POOL_SIZE)

sentry_client = Client(
    settings.SENTRY_SERVER_URL,
    install_sys_hook=False,
    transport=CustomGeventHTTPTransport)

""" g object similar to flask.g but in request context"""
g = None


DEFAULT_ROUTES = [
    ('', 'dashboard.web'),
    ('', 'misc.web'),
    ('/draw', 'draw.web'),
    ('/nodes', 'node.web'),
    ('/domains', 'domain.web'),
    ('/cdn', 'cdn.web'),
    ('/redis', 'redis.web'),
    ('/asset', 'asset.web'),
    ('/privilege', 'privilege.web'),

    ('/users', 'user.handlers'),
    ('/monitor', 'monitor.web'),
    ('/tsdb', 'tsdb.handlers'),
    ('/ocean', 'ocean.handlers'),
    ('/job', 'job.handlers'),

    # ('/raindrop', 'raindrop.web'),

    # APIs
    ('/api/job', 'job.api'),
    ('/api/dashboard', 'dashboard.api'),
    ('/api/draw', 'draw.api'),
    ('/api/nodes', 'node.api'),
    ('/api/domains', 'domain.api'),
    ('/api/servers', 'server.api'),
    ('/api/redis', 'redis.api'),
    ('/api/asset', 'asset.api'),
    ('/api/privilege', 'privilege.api'),

    ('/api/monitor', 'monitor.api'),

    # For backward compatibility
    ('/ptree', 'node.legacy_api'),
    ('/server', 'server.legacy_api'),
]


def init_app(routes=DEFAULT_ROUTES):
    import logging
    from loki import errors
    from loki.utils import encode_json, capture_exception
    from loki.utils.gevent import register_hub_error_handler

    assert getattr(init_app, 'init_flag', False) is False, "loki.app.init_app should not be called twice"

    app.setup()

    # Change settings from ENV
    if os.environ.get('LOKI_DEBUG'):
        logging.info('settings %s changed from ENV: -> %s', 'DEBUG', True)
        app.settings['DEBUG'] = True

    app.register_json_encoder(encode_json)

    app.route_many(routes)

    # In tornado
    @app.register_application_configurator
    def config_sentry(application):
        application.sentry_client = sentry_client

    # In gevent
    @register_hub_error_handler
    def gevent_error_handler(context, exc_info):
        e = exc_info[1]
        if isinstance(e, errors.SentryRequestFailed):
            logging.warn('Send exception to sentry failed: %s', e)
        else:
            capture_exception(exc_info=exc_info)

    global g
    g = local.local()

    app._init_application()

    if settings.DEBUG:
        app.log_app_info()

    init_app.init_flag = True
