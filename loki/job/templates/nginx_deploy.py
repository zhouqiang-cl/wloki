#!/usr/bin/env python
# -*- coding: utf-8 -*-
from loki.job.arguments import TemplateArgument, DeployArgument
from loki.job.base import JobTemplate
from loki.job.templates.template_mixin import make_items, TemplateMixin
from loki.utils import asyncrequest
from loki.errors import FatalError

DEFAULT_BRANCH = [{
    "label": "master", "value": "master"
}]


class NginxDeploy(JobTemplate, TemplateMixin):
    __templatename__ = "nginx_deploy"

    name = TemplateArgument(label=u"模版名称", type="text")
    run_path = TemplateArgument(label=u"运行路径", placeholder=u"默认为运行帐号Home目录",
                                type="text", value="/home/work", required=False)
    user = TemplateArgument(label=u"运行账号", type="text", value="work", required=False)
    timeout = TemplateArgument(label=u"超时时间", type="number", value=120)
    script_path = TemplateArgument(label=u"脚本路径", type="text",
                                   value="/usr/local/bin/op/nginx_deploy.py", required=True, hidden=True)
    branch = DeployArgument(label=u"Git分支", type="select", items=DEFAULT_BRANCH)
    _reload = DeployArgument(label=u"是否通过reload发布, 紧急发布时使用", type="checkbox", value=False, required=True)

    __order__ = [
        "type",
        "name",
        "timeout",
        "contacters",
        "exclude_offline",
        "branch",
        "_reload",
        "servers",
        "concurrence_idc",
        "concurrence_server",
        "pause_after_first_fail"
    ]

    @JobTemplate.deploy_form_hook("branch")
    def change_deploy_branch(self, value):
        try:
            raw = asyncrequest("GET",
                               "http://access.hy01.nosa.me/api/v1/nginx/branches",
                               timeout=2)
            git_branches = raw.json()
        except Exception as e:
            raise FatalError(
                "get git branch from http://access.hy01.nosa.me/api/v1/nginx/branches failed as %s" % e)
        value['items'] = make_items(git_branches)
        return value

    @JobTemplate.dashboard_form_hook("branch")
    def change_dashboard_branch(self, value):
        del value['items']
        value['type'] = "text"
        value['value'] = self.branch
        return value

    def send_deploy_request(self, node_id, confs=None, shelx=False):
        arguments = ["-b", self.branch]
        arguments.extend(["-r", str(self._reload)])
        confs = {
            "run_path": self.run_path,
            "script_path": self.script_path,
            "arguments": arguments,
            "timeout": self.timeout,
            "user": self.user,
        }
        super(NginxDeploy, self).send_deploy_request(node_id, confs, shelx=shelx)
