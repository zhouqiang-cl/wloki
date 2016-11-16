#!/usr/bin/env python
# -*- coding: utf-8 -*-
from loki.job.arguments import TemplateArgument, DeployArgument
from loki.job.base import JobTemplate
from loki.job.templates.template_mixin import TemplateMixin, make_items_by_dict

ACTIONS = {
    u"修改": "modify",
    u"增加": "add"
}


class NginxUpstreamAddOrUpdate(JobTemplate, TemplateMixin):
    __templatename__ = "nginx_upstream_add_or_update"

    name = TemplateArgument(label=u"模版名称", type="text")
    run_path = TemplateArgument(label=u"运行路径", placeholder=u"默认为运行帐号Home目录",
                                type="text", value="/home/work", required=False)
    user = TemplateArgument(label=u"运行账号", type="text", value="work", required=False)
    timeout = TemplateArgument(label=u"超时时间", type="number", value=10)
    script_path = TemplateArgument(label=u"脚本路径", type="text",
                                   value="/usr/local/bin/op/nginx_upstream.py", required=True, hidden=True)
    action = DeployArgument(label=u"执行动作", type="select",
                            items=make_items_by_dict(ACTIONS), required=True)
    upstream_name = DeployArgument(label=u"upstream node名称", type="text", required=True)
    loki_id = DeployArgument(label="loki id", type="number", required=True)
    port = DeployArgument(label=u"端口", type="number", required=True)
    ip_hash = DeployArgument(label=u"是否开启ip_bash", type="checkbox", value=False, required=True)
    online = DeployArgument(label=u"是否在线", type="checkbox", value=True, required=False)

    __order__ = [
        "type",
        "name",
        "timeout",
        "action",
        "upstream_name",
        "loki_id",
        "port",
        "ip_hash",
        "exclude_offline",
        "servers",
        "concurrence_idc",
        "concurrence_server",
        "pause_after_first_fail",
        "script_path"
    ]

    def send_deploy_request(self, node_id, confs=None, shelx=False):
        arguments = []
        arguments.extend([self.action])
        arguments.extend(["-n", self.upstream_name])
        arguments.extend(["-l", str(self.loki_id)])
        arguments.extend(["-p", str(self.port)])
        if self.ip_hash:
            arguments.extend(["-i", "1"])
        else:
            arguments.extend(["-i", "0"])
        if self.online:
            arguments.extend(["-o", "1"])
        else:
            arguments.extend(["-o", "0"])

        confs = {
            "run_path": self.run_path,
            "script_path": self.script_path,
            "arguments": arguments,
            "timeout": self.timeout,
            "user": self.user,
        }
        super(NginxUpstreamAddOrUpdate, self).send_deploy_request(node_id, confs, shelx=shelx)
