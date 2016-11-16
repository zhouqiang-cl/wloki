#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
import re
from lazy_object_proxy.cext import Proxy
import tornado.wsgi
from loki.app import settings, app


def get_wsgi_app():
    from loki.app import init_app, app
    init_app()
    sync_assets_scripts()
    return tornado.wsgi.WSGIAdapter(app.application)


def sync_assets_scripts():
    import uwsgi
    from hashlib import md5

    def update_uwsgi_cache(key, value):
        if uwsgi.cache_exists(key):
            uwsgi.cache_update(key, value)
        else:
            uwsgi.cache_set(key, value)

    curdir = os.path.dirname(os.path.realpath(__file__))
    asset_dir = os.path.join(curdir, settings.ASSET_SCRIPTS_PATH)
    asset_script_paths = [
        d for d in os.listdir(asset_dir)
        if os.path.isfile(os.path.join(asset_dir, d)) and re.match("asset\w+\.py", d)]
    data = {}
    for script_file in asset_script_paths:
        with open(os.path.join(asset_dir, script_file)) as f:
            content = f.read()
            data[script_file] = content
    json_str = app.json_encoder(data)
    update_uwsgi_cache(settings.ASSET_SCRIPTS_CONTENT_KEY, json_str)
    update_uwsgi_cache(settings.ASSET_HASH_KEY, md5(json_str).hexdigest())

wsgi_app = Proxy(get_wsgi_app)


def get_privilege_wsgi_app():
    from loki.app import init_app, app
    init_app([
        ('/api/privilege', 'privilege.api'),
    ])
    return tornado.wsgi.WSGIAdapter(app.application)

privilege_wsgi_app = Proxy(get_privilege_wsgi_app)
