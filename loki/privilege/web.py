#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..base.handlers import BaseHandler


class IndexHandler(BaseHandler):
    def get(self):
        self.render('privilege/index.html')


handlers = [
    ('', IndexHandler),
]
