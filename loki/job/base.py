#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
from loki.base.template import BaseTemplate
from loki.job.statuses import Status
from loki.job.contexts import Context, context_universal_set
from loki.job.models import Template, Deployment
from torext.errors import ValidationError


class JobTemplate(BaseTemplate):

    @classmethod
    def template_form_hook(cls, name):
        return cls.contexts_hook(Context.template_form, name)

    @classmethod
    def deploy_form_hook(cls, name):
        return cls.contexts_hook(Context.deploy_form, name)

    @classmethod
    def dashboard_form_hook(cls, name):
        return cls.contexts_hook(Context.dashboard_form, name)

    def render_template_form(self):
        return self.render_form(Context.template_form)

    def render_deploy_form(self):
        return self.render_form(Context.deploy_form)

    def render_dashboard_form(self):
        return self.render_form(Context.dashboard_form)

    @classmethod
    def get_deployment_by_template(cls, template, parameters):
        deployment = copy.deepcopy(template)
        for name, value in parameters.viewitems():
            if name not in deployment.__templatearguments__:
                setattr(deployment, name, value)
        return deployment

    def __values__(self, contexts):
        """
        :type contexts: collections.Iterable[int]
        :rtype: dict[str, Any]
        """
        return {k: v.get_value() for k, v in self.__arguments__.viewitems()
                if v.get_value() is not None and set(contexts) & v.allow_context}

    @property
    def template_arguments_values(self):
        return self.__values__({Context.template_form})

    @property
    def deploy_arguments_values(self):
        return self.__values__({Context.deploy_form,
                                Context.dashboard_form})

    @property
    def all_arguments_values(self):
        return self.__values__(contexts=context_universal_set)

    @property
    def _key_types(self):
        return {k: v['type'] for k, v in self.__arguments__.viewitems()}

    @property
    def template_name(self):
        return self.__templatename__

    @property
    def __templatearguments__(self):
        return {k: v for k, v in self.__arguments__.viewitems()
                if Context.template_form in v.allow_context}

    def _check_arguments_validation(self, arguments):
        for name, attr in arguments.iteritems():
            # check Argument required attribute
            if name not in self.__arguments__ and attr.get("required"):
                raise ValidationError('key "%s" is required" % name')

            value = getattr(self, name, None)
            if (not value and value is not False) \
                    and attr.get("required") \
                    and not attr.get("null"):
                raise ValidationError('key "%s" not allowed to be null' % name)

    def generate_template_model(self, template=None):
        """
        generate template model according to Template values
        if template isn't None, then inplace changing template parameters
        :type template: Template
        :rtype: Template
        """
        self._check_arguments_validation(self.__templatearguments__)

        kwargs = {
            "name": self.name,
            "type": self.template_name,
            "parameters": self.template_arguments_values,
        }
        if not template:
            template = Template(**kwargs)
        else:
            for k, v in kwargs.iteritems():
                setattr(template, k, v)
        return template

    def generate_deployment_model(self):
        """
        generate deployment model according to Deployment values
        :rtype: Deployment
        """
        self._check_arguments_validation(self.__arguments__)

        kwargs = {
            "id": self.jobset_id,
            "name": self.name,
            "type": self.template_name,
            "parameters": self.deploy_arguments_values,
            "status": int(Status.unknown),
        }
        deployment = Deployment(**kwargs)
        return deployment
