#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..base.handlers import BaseHandler


class HomeHandler(BaseHandler):
    def get(self):
        self.render('dashboard/index.html')


handlers = [
    ('/', HomeHandler),
]
