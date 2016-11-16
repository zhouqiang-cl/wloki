#!/usr/bin/env python
# -*- coding: utf-8 -*-
from loki.job.arguments import TemplateArgument, DeployArgument, TemplateOnlyArgument
from loki.job.contexts import Context
from loki.job.base import JobTemplate
from loki.job.templates.template_mixin import TemplateMixin, make_items, make_items_by_dict

INTERPRETERS = {
    "bash": "/bin/bash",
    "python": "/usr/bin/python",
    "perl": "/usr/bin/perl",
    "ruby": "/usr/bin/ruby",
}


class SimpleScript(JobTemplate, TemplateMixin):
    __templatename__ = "simple_script"

    name = TemplateArgument(label=u"模版名称", type="text")
    run_path = TemplateArgument(label=u"运行路径", placeholder=u"默认为运行帐号Home目录",
                                type="text", value="", required=False, null=True)
    interpreter = TemplateArgument(label=u"解释器", type="select", items=make_items_by_dict(INTERPRETERS))
    user = TemplateArgument(label=u"运行账号", type="text")
    timeout = TemplateArgument(label=u"超时时间", type="number")
    content = TemplateArgument(label=u"脚本内容", type="textarea")
    default_servers = TemplateOnlyArgument(label=u"默认发布机器", type="servers_checkbox",
                                           value=(), required=False)
    default_concurrence_idc = TemplateOnlyArgument(label=u"默认机房间是否并发", type="checkbox",
                                                   value=False, required=False)
    default_concurrence_server = TemplateOnlyArgument(label=u"默认机器间并发度", type="number",
                                                      value=1, required=False)

    debug = DeployArgument(label=u"调试开关", type="checkbox",
                           notice=u"勾选此项且解释器为 bash, 以 bash -x 模式运行脚本",
                           value=False, required=False)

    __order__ = [
        "type",
        "name",
        "user",
        "timeout",
        "interpreter",
        "run_path",
        "content",
        "contacters",
        "exclude_offline",
        "debug",
        "pause_after_first_fail",
        "default_concurrence_idc",
        "default_concurrence_server",
        "default_servers",
        "concurrence_idc",
        "concurrence_server",
        "servers",
    ]

    @JobTemplate.contexts_hook((Context.deploy_form, Context.dashboard_form),
                               "interpreter")
    def remove_interpreter_items(self, value):
        del value['items']
        value['type'] = "text"
        return value

    @JobTemplate.template_form_hook("default_servers")
    def change_template_form_default_servers(self, value):
        value['value'] = self._get_servers_from_node_id(self.node_id, selected_servers=value['value'])
        return value

    @JobTemplate.deploy_form_hook("servers")
    def change_deploy_form_servers(self, value):
        value['value'] = self._get_servers_from_node_id(self.node_id, selected_servers=self.default_servers)
        return value

    @JobTemplate.deploy_form_hook("concurrence_idc")
    def change_deploy_form_concurrence_idc(self, value):
        value['value'] = self.default_concurrence_idc
        return value

    @JobTemplate.deploy_form_hook("concurrence_server")
    def change_deploy_form_concurrence_server(self, value):
        value['value'] = self.default_concurrence_server
        return value

    def send_deploy_request(self, node_id, confs=None, shelx=False):
        arguments = []
        if isinstance(self.content, unicode):
            self.content = self.content.decode("utf8")

        if self.debug and self.interpreter == INTERPRETERS['bash']:
            arguments.extend(["-x"])

        arguments.extend(["-c", r"""%s""" % self.content])

        if not self.run_path:
            self.run_path = "/root" if str(self.user) == "root" else "/home/%s" % self.user

        confs = {
            "run_path": self.run_path,
            "script_path": self.interpreter,
            "arguments": arguments,
            "timeout": self.timeout,
            "user": self.user,
        }
        super(SimpleScript, self).send_deploy_request(node_id, confs, shelx=shelx)
