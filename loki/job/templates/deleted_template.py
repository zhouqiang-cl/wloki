#!/usr/bin/env python
# -*- coding: utf-8 -*-
from loki.job.arguments import TemplateArgument
from loki.job.base import JobTemplate
from loki.job.templates.template_mixin import TemplateMixin
from torext.errors import OperationNotAllowed

notice_info = u"""
此任务模板原型已被删除
请勿更新或发布!
若无必要，请删除此任务模板或发布模板
"""


class DeletedTemplate(JobTemplate, TemplateMixin):
    type = TemplateArgument(type="text", hidden=True, value="deleted_template")
    name = TemplateArgument(label=u"模版名称", type="text", readonly=True)
    info = TemplateArgument(label=u"信息", type="textarea", value=notice_info, readonly=True)

    __order__ = [
        "type",
        "name",
        "info",
        "exclude_offline",
        "servers",
        "concurrence_idc",
        "concurrence_server",
        "pause_after_first_fail",
        "script_path"
    ]

    @property
    def template_name(self):
        return "deleted_template"

    @JobTemplate.dashboard_form_hook("info")
    def change_dashboard_form_info(self, value):
        value["value"] = u"此任务模板原型 %s 已被删除" % self.type
        return value

    def send_deploy_request(self, *args, **kwargs):
        raise OperationNotAllowed("job type deleted_template can't been deployed")
