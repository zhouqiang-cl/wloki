#!/usr/bin/env python
# -*- coding: utf-8 -*-
# jiangchangchun@nosa.me

import re
import json
import requests

from torext import params
from sqlalchemy import and_, or_

from .models import RedisInstance, CodisInstance
from ..db import get_redis
from ..base.handlers import APIHandler
from ..privilege import require_node_privileges
from .privileges import RedisPrivilege


def getDashboardAddr(name):
    """Get codis dashboard address using zk & product_name"""
    tmp = name.split('-')
    cluster, name = tmp[0], tmp[1]
    select_obj = CodisInstance\
                    .query\
                    .filter(and_(CodisInstance.zk == tmp[0],
                        CodisInstance.name == tmp[1]))\
                    .order_by(CodisInstance.zk.asc(),
                        CodisInstance.name.asc())\
                    .limit(1)\
                    .all()
    return cluster, name, select_obj[0].to_dict()['dashboard']


def getRange(data):
    """Get range expression from sequence.
    For example, [1,2,3,6,7,8] produce [[1,3],[6,8]]"""
    if len(data) == 0:
        return []
    data = sorted(data)
    ret = []
    a_range = {'low': data[0], 'high': data[0]}

    for val in data:
        if a_range['high'] == val:
            continue
        elif a_range['high'] + 1 == val:
            a_range['high'] = val
        else:
            ret.append([a_range['low'], a_range['high']])
            a_range['low'] = val
            a_range['high'] = val
    ret.append([a_range['low'], a_range['high']])
    return ret


def check_path(func):
    """Decorator for checking whether the path is allowed by that method"""
    def check_wrapper(self, name, path):
        path = str(path)
        if hasattr(self, 'allow') \
        and func.__name__ in self.allow \
        and not re.match('|'.join(self.allow[func.__name__]), path):
            self.set_status(405)
            self.write('Not allowed path "%s" for method "%s"'%(path, func.__name__))
        else:
            return func(self, name, path)
    return check_wrapper


class ManageHandler(APIHandler):
    """ListRedisHandler list all codis list"""
    allow = {
        'get': ['^list$', '^search$'],
        'post': ['^redis$', '^codis$']
    }

    @check_path
    def get(self, _, path):
        rlt = {}
        if path == "list":
            try:
                select_obj = CodisInstance\
                                .query\
                                .order_by(\
                                    CodisInstance.zk.asc(),\
                                    CodisInstance.name.asc())\
                                .all()
            except Exception as e:
                self.set_status(500)
                self.write(str(e))
            else:
                for o in select_obj:
                    ret = o.to_dict()
                    if not ret['zk'] in rlt:
                        rlt[ret['zk']] = []
                    rlt[ret['zk']].append(ret['name'])

            self.write({'Codis': rlt})
        elif path == "search":
            try:
                keyword = self.get_argument('s');

                obj_codis = CodisInstance\
                                .query\
                                .filter(or_(CodisInstance.name.like("%{0}%".format(keyword)),
                                            CodisInstance.zk.like("%{0}%".format(keyword)),
                                            CodisInstance.dashboard.like("%{0}%".format(keyword)),
                                            CodisInstance.proxy.like("%{0}%".format(keyword))
                                        )\
                                )\
                                .all()
                obj_redis = RedisInstance\
                                .query\
                                .filter(or_(RedisInstance.host.like("%{0}%".format(keyword)),
                                            RedisInstance.port.like("%{0}%".format(keyword)),
                                            RedisInstance.master_host.like("%{0}%".format(keyword)),
                                            RedisInstance.master_port.like("%{0}%".format(keyword)),
                                            RedisInstance.cluster.like("%{0}%".format(keyword))
                                        )\
                                )\
                                .all()
            except Exception as e:
                self.set_status(500)
                self.write(str(e))
            else:
                insensitive_keyword = re.compile(re.escape(keyword), re.IGNORECASE)
                ret = {}
                ret['codis'] = [o.to_dict() for o in obj_codis]
                ret['redis'] = [o.to_dict() for o in obj_redis]
                self.write(json.dumps(ret))

    @require_node_privileges(RedisPrivilege.manage_redis, lambda c: 1)
    @check_path
    def post(self, _, path):
        try:
            try:
                post_data = json.loads(self.request.body)
            except:
                raise ValueError('Invalid post data format')

            if path == "redis":
                p_host = str(post_data['host'])
                p_port = int(post_data['port'])
                p_status = str(post_data['status'])
                RedisInstance.save_and_update(host=p_host, port=p_port, cluster=None, status=p_status, update=True)
            elif path == "codis":
                p_name = str(post_data['name'])
                p_zk = str(post_data['zk'])
                CodisInstance.save_and_update(name=p_name, zk=p_zk, update=True)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
        else:
            self.write(json.dumps({'status': 'success'}))


class DefaultHandler(APIHandler):
    """MainHandler, used for apis not specified separately"""
    allow = {
        'get': ['^overview$']
    }

    @check_path
    def get(self, name, path):
        zk, _, base_url = getDashboardAddr(name)
        url = base_url + "/api/" + path

        try:
            resp = requests.get(url)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
            return

        # Simplefied api for 'overview'
        if path == 'overview':
            ret = {}
            try:
                data = json.loads(resp.text)
            except Exception as e:
                self.set_status(500)
                self.write(str(e))
                return
            else:
                ret['dashboard'] = base_url
                ret['zk'] = zk
                ret['product'] = data['product']
                ret['ops'] = data['ops'] if data['ops'] >= 0 else 0
                ret['keys'], ret['memory'] = (0, 0)
                for redis_info in data['redis_infos']:
                    if redis_info is not None and 'db0' in redis_info:
                        ret['keys'] += int(redis_info['db0'].split(',')[0].split('=')[1])
                        ret['memory'] += int(redis_info['used_memory'])
                self.write(json.dumps(ret))
        else:
            self.write(resp.text)


class DebugHandler(APIHandler):
    """DebugHandler, get codis debug info"""
    def get(self, name, addr):
        if not re.match(r'.+(\.nosajia\.com):\d+', str(addr)):
            tmp = addr.split(":")
            addr = tmp[0] + ".nosa.me:" + tmp[1]
        url = "http://" + addr + "/debug/vars"
        try:
            resp = requests.get(url)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
        else:
            self.write(resp.text)


class GroupHandler(APIHandler):
    """GroupHandler, get & post group info"""
    allow = {
        'get': ['^$'],
        'post': ['^/addGroup$', '^/[0-9]+/addServer$', '^/[0-9]+/removeServer$', '^/[0-9]+/promote$'],
        'delete': ['^/[0-9]+$']
    }

    @check_path
    def get(self, name, path):
        base_url = getDashboardAddr(name)[2]
        url = base_url + "/api/server_groups" + path
        try:
            resp = requests.get(url)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
            return

        ret = []
        for group in json.loads(resp.text):
            grp_data = {}
            grp_data['id'] = group['id']
            grp_data['product_name'] = group['product_name']

            if group['servers'] is not None:
                for server in group['servers']:
                    if server['type'] not in grp_data:
                        grp_data[server['type']] = []
                    url = base_url + "/api/redis/" + server['addr'] + "/stat"

                    serv_data = {}
                    try:
                        resp = requests.get(url)
                        resp_data = json.loads(resp.text)
                    except:
                        serv_data['serv_addr'] = server['addr']
                    else:
                        serv_data['serv_addr'] = server['addr']
                        serv_data['maxmemory'] = resp_data['maxmemory']
                        serv_data['used_memory'] = resp_data['used_memory']
                        if 'db0' in resp_data:
                            serv_data['db0'] = resp_data['db0']
                    grp_data[server['type']].append(serv_data)
            ret.append(grp_data)

        self.write(json.dumps(ret))

    @require_node_privileges(RedisPrivilege.manage_redis, lambda c: 1)
    @check_path
    def post(self, name, path):
        base_url = getDashboardAddr(name)[2]
        if(path == "/addGroup"):
            url = base_url + "/api/server_groups"
        else:
            url = base_url + "/api/server_group" + path

        headers = {'Content-Type': 'application/text; charset=UTF-8'}
        post_data = self.request.body

        try:
            if(re.match(r'^/[0-9]+/promote$', path)):
                resp = requests.post(url, data=post_data, headers=headers)
            else:
                resp = requests.put(url, data=post_data, headers=headers)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
        else:
            self.write(resp.text)

    @require_node_privileges(RedisPrivilege.manage_redis, lambda c: 1)
    @check_path
    def delete(self, name, path):
        base_url = getDashboardAddr(name)[2]
        url = base_url + "/api/server_group" + path
        headers = {'Content-Type': 'application/text; charset=UTF-8'}
        try:
            resp = requests.delete(url, headers=headers)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
        else:
            self.write(resp.text)


class ProxyHandler(APIHandler):
    """ProxyHandler, get & post proxy info"""
    def get(self, name):
        base_url = getDashboardAddr(name)[2]
        url = base_url + "/api/proxy/list"
        try:
            resp = requests.get(url)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
            return
        else:
            self.write(resp.text)

    @require_node_privileges(RedisPrivilege.manage_redis, lambda c: 1)
    def post(self, name):
        base_url = getDashboardAddr(name)[2]
        post_data = ''
        url = base_url + "/api/proxy/list"

        try:
            resp = requests.get(url)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
            return

        for proxy_data in json.loads(resp.text):
            if proxy_data['id'] == self.get_argument('proxy_id'):
                post_data = proxy_data
                break
        if post_data == '':
            self.set_status(500)
            self.write('Not valid proxy_id: %s ' % self.get_argument('proxy_id'))
            return

        # TODO mark_offline not test yet
        if self.get_argument('state') == 'OFF':
            post_data['state'] = 'mark_offline'
        else:
            post_data['state'] = 'online'

        url = base_url + "/api/proxy"
        post_data = json.dumps(post_data)
        headers = {'Content-Type': 'application/json; charset=UTF-8'}

        try:
            resp = requests.post(url, data=post_data, headers=headers)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
        else:
            self.write(resp.text)


class SlotHandler(APIHandler):
    """SlotHandler, get & post slot info"""
    def get(self, name):
        base_url = getDashboardAddr(name)[2]
        url = base_url + "/api/slots"
        try:
            resp = requests.get(url)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
            return

        slots = json.loads(resp.text)
        ret_data = {}
        for slot in slots:
            if slot['group_id'] not in ret_data:
                ret_data[slot['group_id']] = {
                    'group_id': slot['group_id'],
                    'sort_order': 1023,
                    'migrating': [],
                    'offline': [],
                    'online': []
                }
            # 'sort_order' is used for sorting. We wan group list are sorted in minimal slot order.
            if(ret_data[slot['group_id']]['sort_order'] > slot['id']):
                ret_data[slot['group_id']]['sort_order'] = slot['id']

            # 'pre_migrate' status considered to be 'migrating' status.
            if slot['state']['status'] == 'pre_migrate' \
                or slot['state']['status'] == 'migrate':
                ret_data[slot['group_id']]['migrating'].append(slot['id'])
            else:
                ret_data[slot['group_id']][slot['state']['status']].append(slot['id'])

        for k, v in ret_data.iteritems():
            v['migrating'] = getRange(v['migrating'])
            v['offline'] = getRange(v['offline'])
            v['online'] = getRange(v['online'])

        ret_data = ret_data.values()
        self.write(json.dumps(ret_data))

    @require_node_privileges(RedisPrivilege.manage_redis, lambda c: 1)
    def post(self, name):
        base_url = getDashboardAddr(name)[2]
        url = base_url + "/api/slot"
        headers = {'Content-Type': 'application/text; charset=UTF-8'}
        post_data = self.request.body

        try:
            resp = requests.post(url, data=post_data, headers=headers)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
        else:
            self.write(resp.text)


class MigrateHandler(APIHandler):
    """MigrateHandler, migrate slot, show migrate status"""
    allow = {
        'get':['^/status$', '^/tasks$'],
        'post':['^$']
    }

    @check_path
    def get(self, name, path):
        base_url = getDashboardAddr(name)[2]
        url = base_url + "/api/migrate" + path
        try:
            resp = requests.get(url)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
            return
        else:
            if path == '/tasks':
                # Produce compact data
                tmp_data={}
                task_data = json.loads(resp.text)
                if task_data is None or len(task_data) == 0:
                    self.write(resp.text)
                    return
                for task_slot in task_data:
                    tmp_key = '%s-%s-%s-%s-%s'%(task_slot['new_group'],
                                                task_slot['delay'],
                                                task_slot['create_at'],
                                                task_slot['percent'],
                                                task_slot['status'])
                    if tmp_key not in tmp_data:
                        tmp_data[tmp_key] = []
                    tmp_data[tmp_key].append(task_slot['slot_id'])
                rlt = []
                for k, v in tmp_data.iteritems():
                    tmp_arr = k.split('-')
                    if len(v) == 1:
                        slot_ids = v
                    else:
                        tmp_range = getRange(v)[0]
                        print v,tmp_range
                        slot_ids = '%s ~ %s'%(tmp_range[0], tmp_range[1])
                    rlt.append({
                        'slot_id': slot_ids,
                        'new_group': tmp_arr[0],
                        'delay': tmp_arr[1],
                        'create_at': tmp_arr[2],
                        'percent': tmp_arr[3],
                        'status': tmp_arr[4]
                        })
                self.write(json.dumps(rlt))
            else:
                self.write(resp.text)

    @require_node_privileges(RedisPrivilege.manage_redis, lambda c: 1)
    @check_path
    def post(self, name, path):
        base_url = getDashboardAddr(name)[2]
        url = base_url + "/api/migrate"
        headers = {'Content-Type': 'application/text; charset=UTF-8'}
        post_data = self.request.body

        try:
            resp = requests.post(url, data=post_data, headers=headers)
        except Exception as e:
            self.set_status(500)
            self.write(str(e))
            return
        else:
            self.write(resp.text)


handlers = [
    ('/(manage)/(.+)', ManageHandler),
    ('/([\w_-]+)/proxy', ProxyHandler),
    ('/([\w_-]+)/slots', SlotHandler),
    ('/([\w_-]+)/migrate(|/.+)', MigrateHandler),
    ('/([\w_-]+)/server_groups(|/.+)', GroupHandler),
    ('/([\w_-]+)/debug/(.+)', DebugHandler),
    ('/([\w_-]+)/(.+)', DefaultHandler),
]
