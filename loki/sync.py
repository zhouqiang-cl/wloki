#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import socket
import signal
import requests
from requests.exceptions import Timeout
import logging
from collections import defaultdict

import ujson as json
from torext import settings
import gevent
from gevent.monkey import patch_all
from gevent.queue import Queue, Full
from gevent.event import Event
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from kazoo.exceptions import NodeExistsError

from server.models import Server
from node.models import NodeServers
from zookeeper import zk

patch_all()

ASSEST_LOCK_PATH = "/loki/lock/ptree/assets_syncing"
ASSEST_LOCK_TEST_PATH = "/loki/lock/ptree/assets_syncing_test"
ZK_LOCK_PATH = "/loki/lock/ptree/zk_syncing"
PENDING_PATH = '/loki/lock/ptree/sync_pending'

EXIT_CODES = {
    'leave_alone': 9,
    'normal_exit': 0,
    'need_restart': 1
}


def sync_servers_zk(idc_list=None):
    def reducer(x, y):
        if y.server.validity:
            x[y.node_id].append(y.server.hostname)
        return x

    NodeServers.flush()
    servers = NodeServers.query.options(joinedload(NodeServers.server))
    if idc_list:
        servers = servers.filter(NodeServers.node_id.in_(idc_list))

    nodes = defaultdict(list)
    reduce(reducer, servers, nodes)
    for node_id, hostnames in nodes.iteritems():
        zk_servers = set(zk.get_total_servers(node_id, recursive=False))
        if zk_servers != set(hostnames):
            zk.set_node_servers(node_id, *hostnames)


def zk_sync_signal():
    if not zk.exists(ZK_LOCK_PATH):
        return "sync process isn't running"
    if zk.exists(PENDING_PATH):
        zk.set(PENDING_PATH, "")
    else:
        zk.create(PENDING_PATH)


class ServerHelper(object):
    def __init__(self, data):
        self.servers = data

    def subkeys(self, other):
        return set(self.servers.keys()) - set(other.servers.keys())

    def changedkeys(self, other):
        ret = []
        for k, v in self.servers.iteritems():
            new = other.servers.get(k, None)
            if new and new != v:
                ret.append(k)
        return ret


class SyncBaseDeamon(object):

    def __init__(self, interval=5):
        self.ip_addr = socket.gethostbyname(socket.gethostname())
        self.pid = os.getpid()
        self.channel = Queue(1)
        self.sync_interval = int(interval)
        self.exit_flag = Event()
        self.lock_path = ""
        self.logger = logging.getLogger()

    def exit(self):
        if not self.exit_flag.isSet():
            self.exit_flag.set()
            self.channel.put('exit')
        else:
            self.logger.warn("Waiting exit signal been resolved")

    def terminate(self, code):
        zk.close()
        sys.exit(code)

    def run(self):
        greenlets = []
        try:
            zk.create(
                self.lock_path,
                "%s:%s" % (self.ip_addr, self.pid),
                ephemeral=True,
                makepath=True
            )
        except NodeExistsError:
            ret, _ = zk.get(self.lock_path)
            ip, pid = ret.split(':')
            self.logger.error("Servers syncing process is running on %s, pid: %s" % (ip, pid))
            self.terminate(EXIT_CODES['leave_alone'])

        gevent.signal(signal.SIGTERM, self.exit)
        gevent.signal(signal.SIGINT, self.exit)
        gevent.signal(signal.SIGHUP, self.exit)

        greenlets.append(gevent.spawn(self.sync))
        gevent.spawn(self.ticker)

        gevent.joinall(greenlets)
        self.logger.warn("syncing deamon exited")
        self.terminate(EXIT_CODES['normal_exit'])

    def ticker(self):
        while True:
            try:
                if self.channel.qsize() == 0:
                    self.channel.put("sync", block=False)
            except Full:
                self.logger.error("something wrong occur in syncing thread")
                pass
            gevent.sleep(self.sync_interval)

    def sync(self, test=False):
        pass


class SyncAssetsDaemon(SyncBaseDeamon):
    def __init__(self, interval=5):
        super(SyncAssetsDaemon, self).__init__(interval)
        if settings['DEBUG']:
            self.lock_path = ASSEST_LOCK_TEST_PATH
        else:
            self.lock_path = ASSEST_LOCK_PATH
        self.logger = logging.getLogger("assets_syncing_deamon")

    def sync(self, test=False):
        while not self.exit_flag.isSet():
            sig = self.channel.get()
            if sig == "exit":
                self.logger.info("receive exit signal from channel")
                break
            self.logger.info("sync start")
            self._sync(test)
            self.logger.info("sync finished")
            gevent.sleep(1)

    def _sync(self, test=False):
        old_server = self._get_db_servers()
        if not old_server.servers:
            self.init_servers()
        else:
            new_server = self._get_assets_servers()
            if not new_server:
                return
            for k in old_server.subkeys(new_server):
                server = Server.query.filter_by(sn=k).options(joinedload(Server.nodes)).first()
                if server.nodes:
                    for node in server.nodes:
                        if not test:
                            node.delete()
                        self.logger.info("delete server node %s" % node.id)
                try:
                    if not test:
                        server.delete()
                except Exception, e:
                    self.logger.error(e)
                self.logger.info("delete server %s sn %s" % (server.hostname, server.sn))
            for k in old_server.changedkeys(new_server):
                server = Server.query.filter_by(sn=k).first()
                new_name = new_server.servers[k]
                old_name = server.hostname
                server.hostname = new_name
                if not test:
                    try:
                        server.save()
                    except Exception, e:
                        self.logger.error(e)
                self.logger.info("chaneg server %s to %s" % (old_name, new_name))
            for k in new_server.subkeys(old_server):
                server = Server(hostname=new_server.servers[k], sn=k)
                if not test:
                    try:
                        server.save()
                    except Exception, e:
                        self.logger.error(e)
                self.logger.info("add server %s sn %s" % (server.hostname, server.sn))

    def init_servers(self):
        s = self._get_assets_servers()
        _ = lambda x: x.decode("utf8")
        for _server in s.servers:
            try:
                server = Server(hostname=_(_server['hostname']), sn=_(_server['sn']))
                server.save()
            except IntegrityError:
                print "hostname:%s duplicated" % _server['hostname']
                continue

    def _get_db_servers(self):
        Server.flush()
        servers = Server.query.filter_by(validity=True)
        s = ServerHelper(dict([[s.sn, s.hostname] for s in servers]))
        return s

    def _get_assets_servers(self):
        try:
            ret = requests.get("http://t.a.nosa.me/server/api/servers", timeout=30).content
        except Timeout:
            self.logger.error("fetch assets server api timeout")
            return None
        except Exception as e:
            self.logger.error("fetch assets server api error, %s" % e)
            return None
        if ret is None:
            return None
        data = json.loads(ret)
        servers = dict([[s['sn'], s['hostname']] for s in data])
        s = ServerHelper(servers)
        return s


class SyncServersDaemon(SyncBaseDeamon):
    def __init__(self, interval=5):
        super(SyncServersDaemon, self).__init__(interval)
        self.lock_path = ZK_LOCK_PATH

    def sync(self, test=False):
        @zk.DataWatch(PENDING_PATH)
        def watch(data, stat, event=None):
            if event:
                if event.path == PENDING_PATH:
                    try:
                        self.channel.put("sync", block=False)
                    except Full:
                        self.logger.error("something wrong occur in syncing thread")
                        pass

        while not self.exit_flag.isSet():
            sig = self.channel.get()
            if sig == "exit":
                break
            print "syncing"
            sync_servers_zk()
            gevent.sleep(1)
            print "sync end"


if __name__ == "__main__":
    deamon = SyncServersDaemon()
    deamon.run()
