#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import datetime
from ..base.handlers import APIHandler


DOMAIN_WHITELIST = [
    'nosa.me',
    'wdjcdn.com',
    'wdjimg.com',
    'nosa.in',
    'nosa.im',
    'nosajia.cn',
    'nosajia.fm',
    'nosa.com',
    'nosajia.im',
    'nosa.me',
    'snappea.com',
    'snaptubevideo.com',
    'snaptube.in'
]


class DomainsHandler(APIHandler):
    def get(self):
        """
        /tsdb/api/query?type=http&m=zimsum:path.http.qps%7Bdomain=*%7D&start=1m-ago
        """
        from ..tsdb.core import tsdb_query

        # 5 minutes per period
        now = datetime.datetime.now()
        start_dt = now.replace(minute=now.minute - (now.minute % 5))
        start = start_dt.strftime('%Y/%m/%d-%H:%M')

        uri = ('/tsdb/api/query?'
               'type=http&m=zimsum:url.qps%7Bdomain=*%7D'
               '&start=' + start)

        rv = tsdb_query(uri, cache=True, cache_ttl=60 * 5)

        data = []

        ptn = re.compile(r'\.\d+$')
        for i in rv:
            domain = i['tags']['domain']
            # Skip bad domain
            if ptn.search(domain) or not filter(domain.endswith, DOMAIN_WHITELIST):
                continue
            data.append(domain)
        data.sort()

        self.write_data(data)


handlers = [
    ('', DomainsHandler),
]
