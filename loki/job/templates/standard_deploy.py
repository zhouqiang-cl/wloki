#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
from sqlalchemy.orm import aliased

from sqlalchemy.sql.expression import func

from loki.job.arguments import TemplateArgument, DeployArgument, TemplateOnlyArgument
from loki.job.contexts import Context
from loki.job.models import Package
from loki.job.base import JobTemplate
from loki.job.templates.template_mixin import TemplateMixin, make_items
from loki.node.nodes import TreeNode
from loki.settings import DOWNLOAD_URL


class StandardDeploy(JobTemplate, TemplateMixin):
    __templatename__ = "standard_java_deploy"

    name = TemplateArgument(label=u"模版名称", type="text")
    package_name = TemplateArgument(label=u"软件包名", type="select")
    dst = TemplateArgument(label=u"目标目录", type="text")
    pre_command = TemplateArgument(label=u"预先执行", type="text", value="", required=False)
    stop_command = TemplateArgument(label=u"停止脚本", type="text")
    start_command = TemplateArgument(label=u"启动脚本", type="text")
    test_commands = TemplateArgument(label=u"检测命令", type="arrayinput", required=False)
    post_command = TemplateArgument(label=u"最后执行", type="text", value="", required=False)
    timeout = TemplateArgument(label=u"超时秒数", type="number", value=600)
    http_check = TemplateArgument(label=u"7层检测", type="checkbox", value=True, required=False)
    default_servers = TemplateOnlyArgument(label=u"默认发布机器", type="servers_checkbox",
                                           value=(), required=False)
    default_concurrence_idc = TemplateOnlyArgument(label=u"默认机房间是否并发", type="checkbox",
                                                   value=False, required=False)
    default_concurrence_server = TemplateOnlyArgument(label=u"默认机器间并发度", type="number",
                                                      value=1, required=False)

    branch = DeployArgument(label=u"分支名称", type="select")
    script_path = DeployArgument(label=u"发布脚本", type="text", readonly=True,
                                 value='/usr/local/bin/op/deploy.py')
    sleep = DeployArgument(label=u"暂停秒数", type="number", value=10, required=False)

    __order__ = [
        "type",
        "name",
        "package_name",
        "script_path",
        "dst",
        "pre_command",
        "stop_command",
        "start_command",
        "test_commands",
        "post_command",
        "timeout",
        "http_check",
        "contacters",
        "sleep",
        "branch",
        "servers",
        "exclude_offline",
        "default_concurrence_idc",
        "default_concurrence_server",
        "default_servers",
        "concurrence_idc",
        "concurrence_server",
        "pause_after_first_fail",
    ]

    @JobTemplate.template_form_hook("package_name")
    def change_template_package_name(self, value):
        names = [i[0] for i in Package.distinct(Package.name).all()]
        value['items'] = make_items(names)
        return value

    @JobTemplate.contexts_hook((Context.deploy_form, Context.dashboard_form),
                               "package_name")
    def change_deploy_package_name(self, value):
        value.pop('items', None)
        value['type'] = "text"
        return value

    @JobTemplate.dashboard_form_hook("branch")
    def change_dashboard_branch(self, value):
        value.pop('items', None)
        value['type'] = "text"
        return value

    @JobTemplate.deploy_form_hook("branch")
    def change_deploy_branch(self, value):
        subq = Package.query.with_entities(Package.branch.label("branch"),
                                           func.max(Package.ctime).label("max_ctime"))\
            .filter_by(name=self.package_name)\
            .group_by(Package.branch).subquery()
        branches = [i[0] for i in
                    Package.subquery(subq.c.branch)
                        .order_by(subq.c.max_ctime.desc())
                        .limit(20).all()]
        value['items'] = make_items(branches)
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

    def send_deploy_request(self, node_id, confs=None, shelx=True):
        arguments = []
        arguments_dict = {}
        arguments.extend(['-d', self.dst])
        arguments.extend(['--stop-command', '"%s"' % self.stop_command])
        arguments.extend(['--start-command', '"%s"' % self.start_command])
        arguments.extend(['--sleep', '"%s"' % self.sleep])
        # noinspection PyTypeChecker
        for cmd in self.test_commands:
            arguments.extend(['--test-command', '"%s"' % cmd])
        if self.pre_command:
            arguments.extend(['--pre-command', '"%s"' % self.pre_command])
        if self.post_command:
            arguments.extend(['--post-command', '"%s"' % self.post_command])
        if self.verbose:
            arguments.append('--verbose')
        if self.http_check:
            arguments.append('--http-check')

        # Retrieve the most recently added Package record for each idc having certain
        # package_name and branch, split into 2 steps refrain from using complex sql
        idcs = [r[0] for r in
                Package.distinct(Package.idc)
                    .filter_by(name=self.package_name,
                               branch=self.branch).all()]
        for idc in idcs:
            url, target_filename = \
                Package.query.with_entities(Package.url,
                                            Package.target_filename) \
                    .filter_by(name=self.package_name,
                               branch=self.branch,
                               idc=idc) \
                    .order_by(Package.ctime.desc()) \
                    .first()

            arguments_dict[idc] = copy.deepcopy(arguments)
            # url here is a file name, ebooks-webapp-hy-20140506000000.war e.g.
            arguments_dict[idc].append('-s%s/%s' % (DOWNLOAD_URL, url))
            arguments_dict[idc].append('--target-filename "%s"' % target_filename)

        if not arguments_dict:
            raise ValueError("can't get package url from databases")

        confs = {
            "run_path": self.dst,
            "script_path": self.script_path,
            "arguments": arguments_dict,
            "timeout": int(self.timeout),
            "user": "work",
        }
        super(StandardDeploy, self).send_deploy_request(node_id,
                                                        confs,
                                                        shelx=shelx)
