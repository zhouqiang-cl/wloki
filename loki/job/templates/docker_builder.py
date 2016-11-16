#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os import path
from loki.job.base import JobTemplate
from loki.job.arguments import TemplateArgument
from loki.job.templates.template_mixin import TemplateMixin

ENVS = [{"label": 'base', "value": 'base'},
        {"label": 'preonline', "value": 'preonline'},
        {'label': 'online', 'value': 'online'}]


class DockerBuilder(JobTemplate, TemplateMixin):
    __templatename__ = "docker_builder"
    name = TemplateArgument(label=u"模版名称", type="text")
    timeout = TemplateArgument(label=u"超时时间", type="number", value=600)
    repo = TemplateArgument(label=u"Dockerfile目录", type="text")
    env = TemplateArgument(label=u"环境", type="select", items=ENVS)
    packing_host = TemplateArgument(label=u"打包所在机器", type="text", required=False)
    packing_xml = TemplateArgument(label=u"打包xml文件", type="text", required=False)

    __order__ = [
        'type',
        'name',
        'timeout',
        'repo',
        'env',
        'packing_host',
        'packing_xml',
        'contacters',
        'exclude_offline',
        'servers',
        'concurrence_idc',
        'concurrence_server',
        'pause_after_first_fail'
    ]

    def send_deploy_request(self, node_id, confs=None, shelx=True):
        run_path = '/home/work/Dockerfiles/'
        arguments = ['--repo', self.repo]
        if self.env and self.env != 'base':
            arguments.extend(['--env', self.env])
        if self.packing_host:
            arguments.extend(['--packing-host', self.packing_host])
        if self.packing_xml:
            arguments.extend(['--packing-xml', self.packing_xml])

        confs = {
            "run_path": run_path,
            "script_path": path.join(run_path, 'image_builder.py'),
            "arguments": arguments,
            "timeout": int(self.timeout),
            "user": "work",
        }
        super(DockerBuilder, self).send_deploy_request(node_id, confs, shelx)
