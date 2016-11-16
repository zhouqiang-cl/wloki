#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ujson as json
import traceback
from datetime import datetime

from .. import errors
from ..db import get_redis
from ..utils import _3left
from ..utils import asyncrequest
from ..base.handlers import BaseHandler
from ..base.handlers import APIHandler
from ..zookeeper import zk
from ..settings import OPENTSDB_URL
from ..node.models import TrackURL

summary_table_config = [
    {
        'metric_name': 'node.availability',
        'var_name': 'availability',
        'name': 'availability',
    },
    {
        'metric_name': 'node.responsetime',
        'var_name': 'response_time',
        'name': 'response time',
    },
]


class ResourceUsagePercentageHandler(BaseHandler):
    def get(self):
        rds = get_redis()
        data = []
        for _id, percentage in rds.hgetall('home:resource_usage_percentage').items():
            try:
                data.append([zk.without_expire.get_node_name(_id), float(percentage)])
            except:
                pass
        data = sorted(data, key=lambda x: x[1], reverse=True)
        data.append(['other', 100 - sum(map(lambda x:x[1], data))])
        self.write_data(data)


class ProductSummaryHandler(APIHandler):
    def get(self):
        start = self.get_argument('start', None)
        end = self.get_argument('end', None)
        interval = self.get_argument('interval')
        trackurls = TrackURL.query.all()
        product_ids = set(o.to_dict(*['product_id'])['product_id'] for o in trackurls)
        summary = [{"product": str(zk.without_expire.get_node_name(product_id)), \
            "id": product_id} for product_id in product_ids]
        for m in summary_table_config:
            url = (OPENTSDB_URL+'/api/query?m=zimsum:%s' \
                +'{nodeid=%s}') % (m['metric_name'], \
                '|'.join(map(str, product_ids)))
            if start:
                url += '&start='+start
            if end and end != datetime.strftime(datetime.today(), '%Y/%m/%d'):
                url += '&end='+end

            try:
                res = asyncrequest('GET', url, timeout=10)
            except Exception, e:
                traceback.print_exc()
                raise errors.RequestError(str(e))

            if res.status_code != 200:
                self.api_error(res.status_code, res.content)
                return
            response = json.loads(res.content)
            for item in summary:
                for metric in response:
#                    dps = sorted(metric['dps'].iteritems(), key=lambda x: x[1])
                    values = []
                    for p in metric['dps'].iteritems():
                        try:
                            values.append(float(p[1]))
                        except Exception as e:
                            print e
                    if str(metric['tags']['nodeid']) == str(item['id']):
                        if len(values) > 0:
                            item[m['var_name']] = _3left(sum(values)/len(values))
                            break

        vars = map(lambda x: x['var_name'], summary_table_config)
        summary = [item for item in summary if filter(lambda x: x in item, vars)]
        data = dict(
            (conf['var_name'], dict(name=conf['name'], data=[]))
            for conf in summary_table_config
        )
        for item in summary:
            for v in vars:
                if v in item:
                    data[v]['data'].append([item['product'], item[v]])
        for item in data:
            data[item]['data'] = sorted(data[item]['data'], key=lambda x:x[1])
        self.write_data(data)


class ProductIDsHandler(BaseHandler):
    def get(self):
        trackurls = TrackURL.query.all()
        product_ids = set(o.to_dict(*['product_id'])['product_id'] for o in trackurls)
        self.write_data(list(product_ids))


handlers = [
    ('/resource_usage_percentage_summary', ResourceUsagePercentageHandler),
    ('/product_summary', ProductSummaryHandler),
    ('/product_ids', ProductIDsHandler),
]
