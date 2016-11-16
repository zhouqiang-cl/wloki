#!/usr/bin/env python
# -*- coding: utf-8 -*-
from loki.job.arguments import TemplateArgument, DeployArgument
from loki.job.base import JobTemplate
from loki.job.templates.template_mixin import TemplateMixin


class NginxUpstreamDelete(JobTemplate, TemplateMixin):
    __templatename__ = "nginx_upstream_delete"

    name = TemplateArgument(label=u"模版名称", type="text")
    run_path = TemplateArgument(label=u"运行路径", placeholder=u"默认为运行帐号Home目录",
                                type="text", value="/home/work", required=False)
    user = TemplateArgument(label=u"运行账号", type="text", value="work", required=False)
    timeout = TemplateArgument(label=u"超时时间", type="number", value=10)
    action = TemplateArgument(label=u"执行动作", type="text",
                              value="delete", required=True, hidden=True)
    script_path = TemplateArgument(label=u"脚本路径", type="text",
                                   value="/usr/local/bin/op/nginx_upstream.py", required=True, hidden=True)
    upstream_name = DeployArgument(label=u"upstream node名称", type="text", required=True)

    __order__ = [
        "type",
        "name",
        "timeout",
        "upstream_name",
        "exclude_offline",
        "servers",
        "concurrence_idc",
        "concurrence_server",
        "pause_after_first_fail",
    ]

    def send_deploy_request(self, node_id, confs=None, shelx=False):
        arguments = [self.action]
        arguments.extend(["-n", self.upstream_name])
        confs = {
            "run_path": self.run_path,
            "script_path": self.script_path,
            "arguments": arguments,
            "timeout": self.timeout,
            "user": self.user,
        }
        super(NginxUpstreamDelete, self).send_deploy_request(node_id, confs, shelx=shelx)
