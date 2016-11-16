#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import ObjectDeletedError
from loki.job.templates.deleted_template import DeletedTemplate

from torext import params
from ..models import Template
from ...base.template import get_template_types, get_template_by_type
from ...base.handlers import APIHandler
from ...errors import ParamsInvalidError, ValidationError, DoesNotExist
from ..privileges import JobPrivilege
from ...privilege.decorators import require_node_privileges


class TemplateParams(params.ParamSet):
    __datatype__ = 'json'

    type = params.Field(required=True)
    parameters = params.Field(required=True)


class TemplateHandler(APIHandler):
    require_auth = True

    @require_node_privileges(JobPrivilege.manage_template,
                             lambda c: int(c.handler.get_argument('node_id')))
    @TemplateParams.validation_required
    def post(self, tid):
        node_id = self.get_argument("node_id", None)
        if not node_id:
            raise ParamsInvalidError("node_id is needed")
        data = self.params.data
        try:
            template_cls = get_template_by_type(data['type'])
        except KeyError:
            raise ValidationError("job template type %s not found" % data['type'])

        template = Template.query.filter_by(id=tid, node_id=node_id).first()
        if not template:
            raise ValidationError("node_id %d not having this template")
        try:
            template = template_cls(**data['parameters'])\
                .generate_template_model(template)
        except TypeError as e:
            raise ValidationError(str(e))

        template.save()
        self.write_data("update template succeed")

    @require_node_privileges(JobPrivilege.manage_template,
                             lambda c: int(c.handler.get_argument('node_id')))
    def delete(self, tid):
        node_id = self.get_argument("node_id", None)
        if not node_id:
            raise ParamsInvalidError("node_id is needed")
        template = Template.query.filter_by(id=tid, node_id=node_id).first()
        try:
            template.delete()
        except ObjectDeletedError:
            raise DoesNotExist
        self.write_data(None, 204)


class TemplateListHandler(APIHandler):
    require_auth = True

    def get(self):
        node_id = int(self.get_argument("node_id", None))
        if not node_id:
            raise ParamsInvalidError("node_id is needed")
        data = []
        for t in Template.query.filter_by(node_id=node_id).all():
            try:
                template_cls = get_template_by_type(t.type)
            except KeyError:
                template_cls = DeletedTemplate

            template_cls.node_id = node_id
            d = {
                "template_id": t.id,
                "template_name": t.parameters["name"],
                "type": t.type,
                "template_data": template_cls(**t.parameters).render_template_form()
            }
            data.append(d)
        self.write_data(data)

    @require_node_privileges(JobPrivilege.manage_template,
                             lambda c: int(c.handler.get_argument('node_id')))
    @TemplateParams.validation_required
    def put(self):
        data = self.params.data
        node_id = int(self.get_argument("node_id", None))
        if not node_id:
            raise ParamsInvalidError("node_id is needed")
        template_cls = get_template_by_type(data['type'])
        try:
            template = template_cls(**data['parameters']).generate_template_model()
            template.node_id = node_id
        except TypeError as e:
            raise ValidationError(str(e))

        try:
            template.save()
        except IntegrityError:
            raise ValidationError(
                "node_id %d already have template %s" % (template.node_id, template.name))
        self.write_data("create template succeed")


class TemplateTypeHandler(APIHandler):
    require_auth = True

    def get(self):
        node_id = self.get_argument("node_id", None)
        try:
            node_id = int(node_id)
        except Exception as e:
            raise ValidationError("node_id is missed or formatted wrong: %s" % e)
        data = {}
        for k, v in get_template_types().viewitems():
            template = v()
            template.node_id = node_id
            data[k] = template.render_template_form()
        self.write_json(data)


handlers = [
    ('/template', TemplateListHandler),
    ('/template/(\d+)', TemplateHandler),
    ('/template_type', TemplateTypeHandler),
]
