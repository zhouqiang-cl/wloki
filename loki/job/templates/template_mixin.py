#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os import path
import random
import shlex
from collections import defaultdict
import time
import logging
from numbers import Number

from gevent.local import local
from kazoo.exceptions import NodeExistsError, KazooException
from kazoo.protocol.states import EventType

import ujson as json
from loki.base.template import TemplateMeta
from loki.job.arguments import TemplateArgument, DeployArgument
from loki.job.base import JobTemplate
from loki.node.nodes import TreeNode
from loki.job.statuses import Status
from loki.job.models import Deployment
from loki.zookeeper import zk
from loki.errors import FatalError
from loki.settings import ZK_JOB_STATUS_PATH
from loki.settings import ZK_NEW_JOB_PATH
from torext.errors import ValidationError

logger = logging.getLogger("loki.job.templates")

greenlet_local = local()


class TemplateMixin(object):
    __metaclass__ = TemplateMeta

    type = TemplateArgument(type="text", hidden=True, value=lambda self: self.__templatename__)
    concurrence_idc = DeployArgument(label=u"机房间是否并发", type="checkbox")
    concurrence_server = DeployArgument(label=u"机器间并发度", type="number", value=1)
    contacters = TemplateArgument(label=u"通知邮箱", type="arrayinput", required=False, value=[])
    # required by set_servers_from_node
    exclude_offline = TemplateArgument(
        label=u'是否排除 traffic_ratio 为 0 机器',
        notice=u'若勾选，则发布中 traffic_ratio 为 0 机器不可见',
        type="checkbox", value=False)

    servers = DeployArgument(label=u"发布机器", type="servers_checkbox", null=False)
    verbose = DeployArgument(label=u"详细输出", type="checkbox", value=True, required=False)
    pause_after_first_fail = DeployArgument(label=u'失败后立即暂停', type="checkbox", value=True,
                                            required=False)

    # noinspection PyAttributeOutsideInit
    @property
    def jobset_id(self):
        if not getattr(self, "_jobset_id", None):
            self._jobset_id = generate_deploy_id()
        return self._jobset_id

    @property
    def node_id(self):
        if not getattr(self, "_node_id", None):
            raise ValueError("Template/Deployment node_id not set")
        return self._node_id

    # noinspection PyAttributeOutsideInit
    @node_id.setter
    def node_id(self, num):
        assert isinstance(num, int), "node_id should be type int"
        self._node_id = num

    @JobTemplate.deploy_form_hook("servers")
    def change_deploy_form_servers(self, value):
        value['value'] = self._get_servers_from_node_id(self.node_id)
        return value

    def _get_servers_from_node_id(self, node_id, selected_servers=()):
        """
        set template servers from a tree_node
        :param int node_id: node'id which servers belongs to
        """
        tree_node = getattr(greenlet_local, str(node_id), None)
        if not tree_node:
            tree_node = TreeNode(node_id)
            setattr(greenlet_local, str(node_id), tree_node)

        nodes = []
        node_ids = []
        for n in tree_node.dfs_generator():
            node_ids.append(n)
            if n.id == tree_node.id:
                parent = "#"
            else:
                parent = n.parent
            nodes.append({"type": "node",
                          "text": n.name,
                          "id": n.id,
                          "parent": parent})

        if hasattr(self, 'exclude_offline') and self.exclude_offline:
            node_servers = {i for i in tree_node.offspring_nodeservers
                            if i.traffic_ratio != 0}
        else:
            node_servers = tree_node.offspring_nodeservers

        for node_server in node_servers:
            ratio_percent = "{}%".format(node_server.traffic_ratio * 100) \
                if isinstance(node_server.traffic_ratio, Number) else "auto"
            selected = True if node_server.server.hostname in selected_servers else False
            nodes.append({
                "type": "server",
                "text": "{0} ({1})".format(node_server.server.hostname, ratio_percent),
                # NOTE never use `node_server.id` as server type's id because it may collide with node type's id
                "id": '%s:%s' % (node_server.node_id, node_server.server.hostname),
                "hostname": node_server.server.hostname,
                # "idc": tree_node.node_dict[node.node_id]['name'],
                "parent": node_server.node_id,
                "state" : {
                    "selected": selected,
                }
            })
        return nodes

    # def set_deploy_status_watcher(self):
    #     def watcher(event):
    #         if event.type in (EventType.CREATED, EventType.CHANGED):
    #             _d, _ = zk.without_expire.get(job_status_path, watch=watcher)
    #             _s = get_jobset_status(_d)
    #             Deployment.set_status(self.jobset_id, _s)
    #
    #     job_status_path = path.join(ZK_JOB_STATUS_PATH, str(self.jobset_id))
    #     if zk.without_expire.exists(job_status_path, watch=watcher):
    #         _data, _ = zk.without_expire.get(job_status_path, watch=watcher)
    #         status = get_jobset_status(_data)
    #         Deployment.set_status(self.jobset_id, status)

    def send_deploy_request(self, node_id, new_confs, shelx=True):
        confs = {
            "jobset_id": self.jobset_id,
            "servers": self.servers,
            "concurrence_idc": self.concurrence_idc,
            "concurrence_server": self.concurrence_server,
            "pause_after_first_fail": self.pause_after_first_fail,
            "verbose": self.verbose,
        }
        confs.update(new_confs)
        _servers = set(confs['servers'])
        # get all node ids belong to this deployed node.
        # get idc name from hostname temporary
        servers = defaultdict(set)
        for s in _servers:
            idc = s.split(".")[1].rstrip('0123456790')
            servers[idc].add(s)

        jobs = {}
        for idc, hostnames in servers.iteritems():
            if isinstance(confs["arguments"], dict):
                arguments = confs["arguments"].get(idc, None)
            elif isinstance(confs["arguments"], list):
                arguments = confs["arguments"]
            else:
                raise ValidationError("!!! arguments for idc %s is not list or dict !!!" % idc)

            if arguments is None:
                raise ValidationError("!!! arguments for idc %s not exists !!!" % idc)

            if not all([isinstance(a, basestring) for a in arguments]):
                raise ValidationError("!!! arguments for idc %s contains no-string parameters: %s" % (idc, arguments))

            if shelx:
                try:
                    arguments = shlex.split(" ".join(arguments))
                except ValueError as e:
                    raise ValidationError("arguments %s illegal, error: %s" % (arguments, e))

            job = {
                "rundir": confs["run_path"],
                "command": confs["script_path"],
                "argument": arguments,
                "timeout": confs["timeout"],
                "runuser": confs["user"],
                "servers": hostnames
            }
            jobs[idc] = job

        request = {
            "job_set_id": confs["jobset_id"],
            "concurrence_idc": 1 if confs["concurrence_idc"] else 0,
            "concurrence_server": confs["concurrence_server"],
            "jobs": jobs,
            "pause_after_first_fail": confs["pause_after_first_fail"],
        }
        job_path = path.join(ZK_NEW_JOB_PATH, str(confs["jobset_id"]))
        try:
            zk.create(job_path, json.dumps(request), makepath=True)
        except NodeExistsError:
            raise FatalError("!!! job_path %s already exists, attention !!!" % job_path)
        except KazooException, e:
            raise FatalError("!!! %s !!!" % str(e))


def generate_deploy_id():
    return random.randint(100, 921) * 10 ** 16 + int(time.time() * 10 ** 6)


def get_jobset_status(data):
    _status = json.loads(data).get("status", None)
    if not _status:
        return Status.unknown
    else:
        return Status[_status]


def make_items(labels):
    """
    :type labels: collections.Iterable[basestring]
    :rtype: list[dict[basestring, basestring]]
    """
    return [{"label": v, "value": v} for v in labels]


def make_items_by_dict(_dict):
    """
    :type _dict: dict[basestring, basestring]
    :rtype: list[dict[basestring, basestring]]
    """
    return [{"label": l, "value":v} for l, v in _dict.viewitems()]
