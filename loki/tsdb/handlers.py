# -*- coding: utf-8 -*-

from ..base.handlers import APIHandler
from .core import tsdb_query
from . import formatters


class OpenTSDBProxyHandler(APIHandler):
    def get(self):
        plugin = self.get_argument('plugin', 'highcharts')
        typ = self.get_argument('type', 'default')

        rv = tsdb_query(self.request.uri, cache=True)

        if isinstance(rv, list) and not rv:
            self.write_data(rv)
            return

        if plugin == 'highcharts':
            data = formatters.highcharts(rv, typ)
        elif plugin == 'flot':
            data = formatters.flot(rv, typ)
        else:
            data = rv

        self.write_data(data)


handlers = [
    ('/api/query', OpenTSDBProxyHandler),
]
