#!/usr/bin/env python
# -*- coding: utf-8 -*-
from loki.job.arguments import TemplateArgument, DeployArgument
from loki.job.base import JobTemplate
from loki.job.templates.template_mixin import TemplateMixin, make_items


class NginxServer(JobTemplate, TemplateMixin):
    __templatename__ = "nginx_server"

    name = TemplateArgument(label=u"模版名称", type="text")
    run_path = TemplateArgument(label=u"运行路径", placeholder=u"默认为运行帐号Home目录",
                                type="text", value="/home/work", required=False)
    user = TemplateArgument(label=u"运行账号", type="text", value="work", required=False)
    timeout = TemplateArgument(label=u"超时时间", type="number", value=10)
    script_path = TemplateArgument(label=u"脚本路径", type="text",
                                   value="/usr/local/bin/op/nginx_server.py", required=True, hidden=True)
    product = DeployArgument(label=u"产品线", type="select",
                             items=make_items(["ag", "apps", "happiness", "public", "search"]))
    tp = DeployArgument(label=u"内网,外网", type="select", items=make_items(["internal", "external"]))
    idc = DeployArgument(label=u"机房", type="select", items=make_items(["common", "hy", "hlg", "db"]))
    nm = DeployArgument(label=u"文件名", type="text", required=True, placeholder="loki_nosalabs")
    server_names = DeployArgument(label=u"域名", type="text", required=True, placeholder="loki.nosa.me")
    log_format = DeployArgument(label=u"日志格式", type="text", value="main", required=True)
    upstream_node = DeployArgument(label=u"upstream node名称", type="text", required=True, placeholder="loki_nodes")

    __order__ = [
        "type",
        "name",
        "timeout",
        "product",
        "tp",
        "idc",
        "nm",
        "server_names",
        "log_format",
        "upstream_node",
        "exclude_offline",
        "servers",
        "concurrence_idc",
        "concurrence_server",
        "pause_after_first_fail",
        "script_path"
    ]

    def send_deploy_request(self, node_id, confs=None, shelx=False):
        log_name = self.nm
        arguments = []
        arguments.extend(["-p", self.product])
        arguments.extend(["-t", self.tp])
        arguments.extend(["-i", self.idc])
        arguments.extend(["-n", self.nm])
        arguments.extend(["-s", self.server_names])
        arguments.extend(["-a", log_name])
        arguments.extend(["-o", self.log_format])
        arguments.extend(["-u", self.upstream_node])

        confs = {
            "run_path": self.run_path,
            "script_path": self.script_path,
            "arguments": arguments,
            "timeout": self.timeout,
            "user": self.user,
        }
        super(NginxServer, self).send_deploy_request(node_id, confs, shelx=shelx)
