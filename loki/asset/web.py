#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..base.handlers import BaseHandler


class IndexHandler(BaseHandler):
    def get(self):
        self.render('asset/index.html')


class ServerSNHandler(BaseHandler):
    def get(self, sn):
        self.render('asset/server.html', sn=sn)


handlers = [
    ('', IndexHandler),
    # %3A is `:` (colon) in url encode
    (r'/sn%3A([\w-]+)', ServerSNHandler),
]
