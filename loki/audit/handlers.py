#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..base.handlers import BaseHandler


class DemoHandler(BaseHandler):
    def get(self):
        pass


handlers = [
    ('/', DemoHandler),
]
