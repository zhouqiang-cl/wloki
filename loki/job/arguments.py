#!/usr/bin/env python
# -*- coding: utf-8 -*-
from loki.base.template import Argument
from loki.job.contexts import Context


class JobArgument(Argument):
    allow_context = ()

    def __init__(self, **kwargs):
        super(JobArgument, self).__init__(**kwargs)
        self._dict.setdefault("required", True)
        self._dict.setdefault("null", False)
        self._context = None

    def set_context(self, context):
        if context not in self.allow_context:
            return False
        if context is Context.dashboard_form and self['key'] in ('servers', 'type'):
            return False
        self._context = context

    def get_value(self):
        return self._dict.get('value')

    def for_json(self):
        _dict = super(JobArgument, self).for_json()
        if _dict.get('value') is not None \
                and _dict['type'] == "dictinput":
            _dict.__setitem__('items', self._make_kv_items(_dict['value']))
            del _dict['value']
        return _dict

    @staticmethod
    def _make_kv_items(value):
        """
        :type value: dict
        :rtype: list[dict]
        """
        return [{"key": k, "value": v} for k, v in value.viewitems()]


class TemplateArgument(JobArgument):
    allow_context = {Context.template_form,
                     Context.deploy_form,
                     Context.dashboard_form}

    def for_json(self):
        _dict = super(TemplateArgument, self).for_json()
        if self._context in (Context.deploy_form, Context.dashboard_form):
            _dict.__setitem__('readonly', True)
        return _dict


class TemplateOnlyArgument(JobArgument):
    allow_context = {Context.template_form}


class DeployArgument(JobArgument):
    allow_context = {Context.deploy_form,
                     Context.dashboard_form}

    def for_json(self):
        _dict = super(DeployArgument, self).for_json()
        if self._context is Context.dashboard_form:
            _dict.__setitem__('readonly', True)
        return _dict
