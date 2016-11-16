#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from poseidon.providers.interface import ProviderInterface
from poseidon.acl.interface import ACLInterface
from poseidon.watchdog.networkbench import NetworkBench

from ..base.handlers import BaseHandler
from ..privilege import require_node_privileges
from .privileges import CDNPrivilege



class IndexHandler(BaseHandler):
    def get(self):
        self.render('cdn/index.html')


class BandwidthHandler(BaseHandler):
    @require_node_privileges(CDNPrivilege.view_cdn, lambda c: 1)
    def get(self):
        start_date, end_date = self.get_argument('fd', None), self.get_argument('td', None)
        if not start_date or not end_date:
            start_date, end_date = '0', '0'
        try:
            start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').strftime('%s')) * 1000
            end_ts = int((datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%s')) * 1000
        except ValueError:
            start_ts = 'now-7d'
            end_ts = 'now'
        self.render('cdn/bandwidth.html', start_ts=start_ts, end_ts=end_ts)


class BandwidthQueryHandler(BaseHandler):
    @require_node_privileges(CDNPrivilege.view_cdn, lambda c: 1)
    def post(self):
        start_date = self.get_body_argument('from')
        end_date = self.get_body_argument('to')
        self.redirect('/cdn/bandwidth?fd={}&td={}'.format(start_date, end_date))


class PurgerHandler(BaseHandler):
    @require_node_privileges(CDNPrivilege.view_cdn, lambda c: 1)
    def get(self):
        self.render('cdn/purger.html')

    @require_node_privileges(CDNPrivilege.manage_cdn, lambda c: 1)
    def post(self):
        urls = self.get_body_argument('urls')
        url_list = urls.split()
        provider_name = self.get_body_argument('provider')
        provider_interface = ProviderInterface(provider_name)
        result_msg = provider_interface.purge(url_list)
        self.render(
            'cdn/purger_submit.html',
            result_msg=result_msg
        )


class WatchdogHandler(BaseHandler):
    @require_node_privileges(CDNPrivilege.view_cdn, lambda c: 1)
    def get(self):
        fd = self.get_query_argument('fd', '')
        td = self.get_query_argument('td', '')
        self.render('cdn/watchdog.html', fd=fd, td=td)


class WatchdogChartHandler(BaseHandler):
    @require_node_privileges(CDNPrivilege.view_cdn, lambda c: 1)
    def get(self):
        chart_id = self.get_query_argument('chart_id')
        task_id = self.get_query_argument('task_id')
        fd = self.get_query_argument('fd', None)
        td = self.get_query_argument('td', None)
        nb = NetworkBench()
        chart = nb.get_chart(chart_id, task_id, fd, td)
        self.render('cdn/watchdog_chart.html', chart=chart)


class ACLHandler(BaseHandler):
    @require_node_privileges(CDNPrivilege.view_cdn, lambda c: 1)
    def get(self):
        acl = ACLInterface()
        acl_table = acl.get_acl_table()
        self.render(
            'cdn/acl.html',
            acl_table=acl_table
        )

    @require_node_privileges(CDNPrivilege.manage_cdn, lambda c: 1)
    def post(self):
        domain = self.get_body_argument('domain')
        user = self.get_body_argument('user')
        action = self.get_body_argument('action')
        acl = ACLInterface()
        if action == 'add':
            acl.add_user(domain, user)
        elif action == 'del':
            acl.del_user(domain, user)
        else:
            raise NotImplementedError
        self.redirect('/cdn/acl')


handlers = [
    ('', IndexHandler),
    (r'/bandwidth', BandwidthHandler),
    (r'/bandwidth/query', BandwidthQueryHandler),
    (r'/purger', PurgerHandler),
    (r'/purger/submit', PurgerHandler),
    (r'/watchdog', WatchdogHandler),
    (r'/watchdog/chart', WatchdogChartHandler),
    (r'/acl', ACLHandler)
]
