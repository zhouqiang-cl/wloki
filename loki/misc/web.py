#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
# from markdown import markdown
import mistune
from ..base.handlers import BaseHandler


class ReadmeHandler(BaseHandler):
    def get(self):
        import sys
        reload(sys)
        sys.setdefaultencoding('utf8')
        readme_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../README.md')
        # readme = markdown(open(readme_file).read().encode('UTF-8'), safe_mode="escape", extensions=['tables'])
        readme = mistune.markdown(open(readme_file).read().encode('UTF-8'))
        self.render('misc/readme.html', readme=readme)


class TestSentryHandler(BaseHandler):
    require_auth = False

    def get(self):
        raise Exception('wtffff <tag>')

    def post(self):
        import gevent

        def raise_err():
            raise ValueError('a')

        g = gevent.spawn(raise_err)

        print 'Greenlet:', g
        print g.parent

        gevent.joinall([g])


class TestError(BaseHandler):
    require_auth = False

    def get(self):
        1 / 0

    def post(self):
        1 / 0

    def put(self):
        1 / 0

    def delete(self):
        1 / 0


handlers = [
    ('/readme', ReadmeHandler),
    ('/_test_sentry', TestSentryHandler),
    ('/_test_error', TestError),
]
