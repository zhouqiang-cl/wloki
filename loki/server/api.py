#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
import fractions
from numbers import Number
import itertools
from lazy_object_proxy import Proxy
from decimal import Decimal as D

import gevent
from sqlalchemy.orm import joinedload

from ..errors import ValidationError, TemporaryServerError
from ..base.handlers import APIHandler
from loki.app import greenlet_pool
from ..node.models import NodeServers
from ..zookeeper import zk
from .models import RawServer
from loki.utils.frozendict import FrozenDict


def _get_path_servers(path=None):
    tree_dirs = zk.without_expire.get_dirs_meta()
    if path is None:
        node_servers = NodeServers.query.options(
            joinedload(NodeServers.server).load_only('id', 'hostname')).all()
        node_dirs = dict((v, k) for k, v in tree_dirs.items())
        data = defaultdict(list)
        for node in node_servers:
            try:
                data[node_dirs[node.node_id]].append({"hostname": node.server.hostname,
                                                      "id": node.server.id})
            except KeyError:
                pass
    else:
        node_ids = []
        if path not in tree_dirs:
            return None
        for _path, node_id in tree_dirs.iteritems():
            if _path.startswith(path + '/') or _path == path:
                node_ids.append(node_id)
        node_servers = NodeServers.get_by_node_ids(node_ids)
        if len(node_servers) == 0:
            return None
        data = set()
        data |= set([FrozenDict(hostname=n.server.hostname,
                                id=n.server.id) for n in node_servers])
    return list(data)


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class ServersHandler(APIHandler):
    require_auth = False
    wait_timeout_s = 2

    class NodeServersProxy(Proxy):
        def __init__(self, wrapped):
            def wrapped_func():
                return wrapped
            wrapped._compeers = []
            super(ServersHandler.NodeServersProxy, self).__init__(wrapped_func)

        @property
        def compeers(self):
            assert len(self._compeers) != 0, "node_servers compeers should be 1 at least"
            return self._compeers

        @compeers.setter
        def compeers(self, value):
            self._compeers = value

        def nonzero_num(self):
            return len(filter(lambda x: x.traffic_ratio != 0, self.compeers))

        def traffic_ratio_sum(self):
            return sum([n.traffic_ratio for n in self.compeers if n.traffic_ratio is not None])

        def null_num(self):
            return len(filter(lambda x: x.traffic_ratio is None, self.compeers))

        # @property
        def weight(self):
            if self.traffic_ratio is None:
                _ret = round(self.nonzero_num() * D("1000") * (D("1") - self.traffic_ratio_sum()) / self.null_num())
            else:
                _ret = self.nonzero_num() * D("1000") * self.traffic_ratio
            return int(_ret)

        def __hash__(self):
            return hash(self.__wrapped__.server.hostname)

        def __eq__(self, other):
            return self.__wrapped__.server.hostname == other.server.hostname

    def get(self):
        typ = self.get_argument('type', 'node')
        with_weight = bool(self.get_argument('with_weight', 0))
        node_id = int(self.get_argument('node_id', 0))
        handle_func = getattr(self, "handle_{}".format(typ), None)
        if handle_func is None:
            raise ValidationError("query type invalid")
        ret = handle_func(node_id, with_weight)
        self.write_data(ret)

    def handle_node(self, node_id, *args):
        _args = ['id', 'hostname']
        nodes = NodeServers.get_by_node_id(node_id=node_id)
        ret = []
        if nodes:
            for o in nodes:
                item = o.server.to_dict(*_args)
                item['traffic_ratio'] = str(o.traffic_ratio) \
                    if isinstance(o.traffic_ratio, Number) else None
                ret.append(item)
        return ret

    def handle_path(self, *args):
        path = self.get_argument('path', None)
        if path is None:
            ret = _get_path_servers()
        else:
            if isinstance(path, str):
                path = path.decode("utf8")
            path = path.rstrip('/')
            ret = _get_path_servers(path)
            if ret is None:
                raise ValidationError("path %s doesn't exists" % path)
        return ret

    def handle_available(self, *args):
        all_servers = RawServer.valid().options(joinedload(RawServer.nodes)).all()
        ret = [{
            "hostname": o.hostname,
            "idc_ids": [n.node_id for n in o.nodes]
        } for o in all_servers]
        return ret

    def handle_recursive(self, node_id, with_weight, *args):
        picker = {
            "id": lambda x: x.server_id,
            "hostname": lambda x: x.server.hostname,
            # "traffic_ratio": lambda x: None if x.traffic_ratio is None else str(x.traffic_ratio),
        }
        # 给 draw
        node_ids = set(zk.without_expire.get_node_children(node_id, recursive=True))
        node_servers = {
            self.NodeServersProxy(n)
            for n in NodeServers.get_by_node_ids(node_ids)
        }
        if with_weight:
            gcd = 0
            for key, node_group in itertools.groupby(sorted(node_servers, key=lambda x: x.node_id),
                                                     lambda x: x.node_id):
                node_group = list(node_group)
                for node_server in node_group:
                    node_server.compeers = node_group
                    gcd = fractions.gcd(gcd, node_server.weight())

            picker.update({
                "weight": lambda x: x.weight() / gcd,
            })

        ret = [{k: f(o) for k, f in picker.iteritems()}
               for o in node_servers]
        return ret

    def handle_group(self, *args):
        # 给 Zhouqiang
        def callback_factory(_data):
            def callback(_value):
                key = ":".join((str(i) for i in _value))
                ret[key].append(_data)

            return callback

        def reducer(x, y):
            x[y.node_id].append(y.server.hostname)
            return x

        node_servers = NodeServers._make_get_by_node_query()
        data = defaultdict(list)
        reduce(reducer, node_servers, data)
        ret = defaultdict(list)
        cache = {}
        greenlets = []
        for node_id, value in data.iteritems():
            _func = callback_factory({"idc_id": node_id, "hostnames": value})
            free_num = greenlet_pool.wait_available(timeout=self.wait_timeout_s)
            if free_num == 0:
                raise TemporaryServerError("Waiting for idle Greenlet Timeout after %s seconds"
                                           % self.wait_timeout_s)
            greenlet = greenlet_pool.apply_async(zk.without_expire.get_node_parents_ids,
                                                 args=(node_id, cache),
                                                 callback=_func)
            greenlets.append(greenlet)
        gevent.joinall(greenlets)
        ret = dict(ret)
        return ret


handlers = [
    ('', ServersHandler),
]
