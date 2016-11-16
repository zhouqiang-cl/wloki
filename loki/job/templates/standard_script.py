#!/usr/bin/env python
# -*- coding: utf-8 -*-
from loki.job.arguments import TemplateArgument
from loki.job.base import JobTemplate
from loki.job.templates.template_mixin import TemplateMixin


class StandardScript(JobTemplate, TemplateMixin):
    __templatename__ = "standard_script"

    name = TemplateArgument(label=u"模版名称", type="text")
    script_path = TemplateArgument(label=u"脚本路径", type="text")
    run_path = TemplateArgument(label=u"运行路径", type="text")
    user = TemplateArgument(label=u"运行账号", type="text")
    timeout = TemplateArgument(label=u"超时时间", type="number")
    arguments = TemplateArgument(label=u"脚本参数", type="arrayinput", required=False)

    __order__ = [
        "type",
        "name",
        "script_path",
        "run_path",
        "user",
        "timeout",
        "arguments",
        "contacters",
        "exclude_offline",
        "servers",
        "concurrence_idc",
        "concurrence_server",
        "pause_after_first_fail"
    ]

    def send_deploy_request(self, node_id, confs=None, shelx=True):
        confs = {
            "run_path": self.run_path,
            "script_path": self.script_path,
            "arguments": self.arguments,
            "timeout": self.timeout,
            "user": self.user,
        }
        super(StandardScript, self).send_deploy_request(node_id, confs, shelx=shelx)
