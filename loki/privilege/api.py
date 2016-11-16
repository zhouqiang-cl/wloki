#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
from sqlalchemy.orm import undefer_group
from sqlalchemy.exc import IntegrityError
from torext import params

from loki import errors
from loki.app import settings
from loki.base.handlers import APIHandler
from loki.base.privileges import get_all_privileges_items, get_privilege_by_name, PrivilegeGroup
from loki.node.nodes import TreeNode
from loki.privilege.models import PrivilegeType, PrivilegeStatus, authorize
from loki.privilege.privileges import GrantingPrivilege
from ..utils.cipher import encrypt_token, decrypt_token


class OverViewHandler(APIHandler):
    def get(self):
        privilege_types = []
        for name, privilege in get_all_privileges_items():
            privilege_types.append({
                "name": name,
                'alias': privilege.get_alias(),
                "privileges": [{
                    "name": privilege_name,
                    "description": p.value.desc
                } for privilege_name, p in privilege.enum.__members__.items()]
            })
        self.write_json({'privilege_types': privilege_types})


class ApplyParams(params.ParamSet):
    __datatype__ = "json"
    node_id = params.IntegerField(required=True)
    privilege_type = params.WordField(required=True)
    privilege_names = params.ListField(
        item_field=params.RegexField(pattern=r'[\w_-]+'))
    token = params.Field()

    def validate_privilege_type(self, data):
        try:
            return get_privilege_by_name(data)
        except KeyError:
            raise errors.ValidationError("privilege_type %s not existed" % data)

    def validate_token(self, value):
        if value:
            if not decrypt_token(value, settings.AUTH_TOKEN_PREFIX):
                raise errors.ValidationError('Invalid token value')
        return value


class PetitionApplyHandler(APIHandler):
    require_auth = True

    @ApplyParams.validation_required
    def post(self, type):
        handler = getattr(self, type, None)
        if not handler:
            raise errors.DoesNotExist()
        else:
            return handler()

    def apply_token(self):
        privilege_type = self.params.privilege_type
        privilege = privilege_type()
        for privilege_name in privilege.enum.__members__.keys():
            if privilege_name == "admin":
                continue
            privilege.set_matrix_by_name(privilege_name, PrivilegeStatus.applying)

        prefixed_token = self.params.token
        if not prefixed_token:
            prefixed_token = encrypt_token(self.user.username)

        privilege_model = PrivilegeType(node_id=self.params.node_id,
                                        username=prefixed_token,
                                        privilege_cls=privilege)
        try:
            privilege_model.save()
        except IntegrityError:
            raise errors.ParamsInvalidError('Token has already been applied for this privilege')
        return self.write_json({"message": "apply token succeed"})

    def apply(self):
        privilege_type = self.params.privilege_type
        privilege_names = self.params.privilege_names
        if not privilege_names:
            raise errors.ParamsInvalidError("privilege_names is required")

        privilege_model = PrivilegeType.query.filter_by(node_id=self.params.node_id,
                                                        username=self.user.username,
                                                        privilege_type=privilege_type.name).first()

        if privilege_model:
            privilege = privilege_model.privileges
            for privilege_name in privilege_names:
                status = privilege.get_matrix_by_name(privilege_name)
                if status == PrivilegeStatus.applying:
                    raise errors.OperationNotAllowed("user %s have been applying <%s %s> on node id %s" % (
                        self.user.username, privilege_type.name, privilege_name, self.params.node_id
                    ))
                elif status == PrivilegeStatus.approved:
                    raise errors.OperationNotAllowed("user %s have been granted <%s %s> on node id %s" % (
                        self.user.username, privilege_type.name, privilege_name, self.params.node_id
                    ))
                else:
                    privilege.set_matrix_by_name(privilege_name, PrivilegeStatus.applying)
            privilege_model.privileges = privilege
        else:
            privilege = privilege_type()
            for privilege_name in privilege_names:
                privilege.set_matrix_by_name(privilege_name, PrivilegeStatus.applying)
            privilege_model = PrivilegeType(node_id=self.params.node_id,
                                            username=self.user.username,
                                            privilege_cls=privilege)
        privilege_model.save()
        return self.write_json({"message": "apply privilege succeed"})


class PetitionParams(params.ParamSet):
    __datatype__ = "json"
    privilege_id = params.IntegerField(required=True)
    privilege_name = params.RegexField(pattern=r'[\w_-]+', required=True)
    node_id = params.Field()
    privilege_model = params.Field()

    def validate_privilege_id(self, pid):
        self.data['privilege_model'] = PrivilegeType.query.options(undefer_group("audit")).get_or_raise(pid)
        self.data['node_id'] = int(self.privilege_model.node_id)
        return pid


class PetitionHandler(APIHandler):
    require_auth = True
    privilege_map = {
        PrivilegeGroup.normal: GrantingPrivilege.grant_normal_privileges,
        PrivilegeGroup.critical: GrantingPrivilege.grant_critical_privileges,
    }

    @PetitionParams.validation_required
    def post(self, action):
        handler = getattr(self, "{}_handler".format(action), None)
        if handler is None:
            raise errors.ParamsInvalidError("petition action {} invalid".format(action))
        else:
            return handler(self.params.privilege_model, self.params.privilege_name)

    def _generic_handler(self, privilege_model, privilege_name, action, from_statuses, to_status):
        """
        :type privilege_model: loki.privilege.models.PrivilegeType
        :type privilege_name: str
        :type action: str
        :type from_statuses: list[loki.privilege.models.PrivilegeStatus]
        :type to_status: loki.privilege.models.PrivilegeStatus
        """
        privileges = privilege_model.privileges
        if privilege_name == "admin":
            required_privilege = self.privilege_map[privileges.group]
            """
            check grant_normal_privileges or grant_critical_privileges
            when applying admin privilege
            """
            authorize(required_privilege, self.user.username, node_id=self.params.node_id)
        else:
            required_privilege = getattr(privileges, "admin")
            """
            check corresponding admin privilege
            when applying other privileges
            """
            authorize(required_privilege, self.user.username, node_id=self.params.node_id)

        try:
            status = PrivilegeStatus(privileges.get_matrix_by_name(privilege_name))
            if status not in from_statuses:
                raise errors.OperationNotAllowed("can't {} petition in {} status".format(action, status.name))
            else:
                privileges.set_matrix_by_name(privilege_name, to_status)
                privilege_model.privileges = privileges
                privilege_model.modifier = self.user.username
                privilege_model.save()
        except AttributeError as e:
            raise errors.ParamsInvalidError(str(e))
        else:
            return self.write_json(privilege_model.for_json())

    def approve_handler(self, privilege_model, privilege_name):
        self._generic_handler(privilege_model,
                              privilege_name,
                              action="approve",
                              from_statuses=[PrivilegeStatus.applying, PrivilegeStatus.rejected, PrivilegeStatus.revoked],
                              to_status=PrivilegeStatus.approved)

    def reject_handler(self, privilege_model, privilege_name):
        self._generic_handler(privilege_model,
                              privilege_name,
                              action="reject",
                              from_statuses=[PrivilegeStatus.applying],
                              to_status=PrivilegeStatus.rejected)

    def revoke_handler(self, privilege_model, privilege_name):
        self._generic_handler(privilege_model,
                              privilege_name,
                              action="revoke",
                              from_statuses=[PrivilegeStatus.approved],
                              to_status=PrivilegeStatus.revoked)


def format_paginator_resposne(data, count, limit, index):
    return {
        'data': data,
        'count': count,
        'limit': limit,
        'index': index,
        'pages': math.ceil(count / float(limit)),
    }


class UserPrivilegeHandler(APIHandler):
    require_auth = True

    def get(self):
        privilege_type = self.get_argument('type', None)
        limit = int(self.get_argument('limit', 0))
        index = int(self.get_argument('index', 1))
        username = self.user.username

        privilege_types = PrivilegeType.query.options(undefer_group("audit"))\
            .filter_by(username=username).order_by(PrivilegeType.ctime.desc())

        if privilege_type:
            privilege_types = privilege_types.filter_by(privilege_type=privilege_type)

        if limit:
            count, privilege_types = privilege_types.paginator(limit, index)

            data = privilege_types.all()
            self.write_json(
                format_paginator_resposne(
                    data, count, limit, index)
            )
        else:
            self.write_data(privilege_types.all())


class NodeUserPrivilegeHandler(APIHandler):
    require_auth = True

    def get(self, node_id, type):
        privilege_type = self.get_argument('type', None)
        limit = int(self.get_argument('limit', 0))
        index = int(self.get_argument('index', 1))
        node_id = int(node_id)
        node = TreeNode(node_id)

        privilege_types = PrivilegeType.query \
            .options(undefer_group("audit")) \
            .order_by(PrivilegeType.ctime.desc())
        if type == "user":
            node_ids = [n.id for n in node.parents]
            node_ids.append(node.id)
            privilege_types = privilege_types \
                .filter(PrivilegeType.node_id.in_(node_ids)) \
                .filter_by(username=self.user.username)
        elif type == "token":
            node_ids = [n.id for n in node.offspring_treenode]
            privilege_types = privilege_types \
                .filter(PrivilegeType.node_id.in_(node_ids)) \
                .filter(PrivilegeType.username.like(settings.AUTH_TOKEN_PREFIX + "%"))

        if privilege_type:
            privilege_types = privilege_types.filter_by(privilege_type=privilege_type)

        if limit:
            count, privilege_types = privilege_types.paginator(limit, index)
            data = privilege_types.all()
            self.write_json(
                format_paginator_resposne(
                    data, count, limit, index)
            )
        else:
            self.write_data(privilege_types.all())


class NodePrivilegeHandler(APIHandler):
    require_auth = True

    def get(self, node_id):
        privilege_type = self.get_argument('type', None)
        status_str = self.get_argument('status', None)
        limit = int(self.get_argument('limit', 0))
        index = int(self.get_argument('index', 1))
        username = self.get_argument('username', None)

        privilege_types = PrivilegeType.query.options(undefer_group("audit")) \
            .filter(~PrivilegeType.username.like(settings.AUTH_TOKEN_PREFIX + "%")) \
            .order_by(PrivilegeType.ctime.desc())

        if username:
            privilege_types = privilege_types.filter(PrivilegeType.username == username)

        node_id = int(node_id)
        if node_id != settings.TREE_ROOT_ID:
            node = TreeNode(node_id)
            node_ids = [n.id for n in node.offspring_treenode]
            privilege_types = privilege_types.filter(PrivilegeType.node_id.in_(node_ids))

        if status_str:
            try:
                status = PrivilegeStatus[status_str]
            except KeyError:
                raise errors.ParamsInvalidError("status %s invalid" % status_str)
            status_mask = status.value * sum(2 ** i for i in xrange(0, 64, 4))
            privilege_types = privilege_types.filter(PrivilegeType._matrix.op('&')(status_mask) != 0b0)

        if privilege_type:
            privilege_types = privilege_types.filter_by(privilege_type=privilege_type)

        if limit:
            count, privilege_types = privilege_types.paginator(limit, index)
            data = privilege_types.all()
            self.write_json(
                format_paginator_resposne(
                    data, count, limit, index)
            )
        else:
            self.write_data(privilege_types.all())


class AuthorizeParams(params.ParamSet):
    __datatype__ = "json"
    privilege_type = params.WordField(required=True)
    privilege_name = params.RegexField(pattern=r'[\w_-]+', required=True)
    username = params.Field()
    hostname = params.Field()
    node_id = params.IntegerField()
    token = params.Field()

    def validate_privilege_type(self, value):
        try:
            return get_privilege_by_name(value)
        except KeyError:
            raise errors.ValidationError("privilege_type %s not existed" % value)


class AuthorizeHandler(APIHandler):

    @AuthorizeParams.validation_required
    def post(self):
        if self.user:
            username = self.user.username
        else:
            username = self.params.username
            if not username:
                raise errors.ParamsInvalidError('username must be passed')

        privilege = getattr(self.params.privilege_type, self.params.privilege_name, None)
        if not privilege:
            raise errors.ParamsInvalidError("Invalid type of privilege: <%s %s>" % (self.params.privilege_type.name,
                                                                                    self.params.privilege_name))
        authorize(privilege, username, node_id=self.params.node_id, hostname=self.params.hostname)

        return self.write_json({"msg": "authorize succeed"})


handlers = [
    ('/overview', OverViewHandler),
    ('/petition/(reject|revoke|approve)', PetitionHandler),
    ('/petition/(apply|apply_token)', PetitionApplyHandler),
    ('/user', UserPrivilegeHandler),
    ('/nodes/(\d+)', NodePrivilegeHandler),
    ('/nodes/(\d+)/(user|token)', NodeUserPrivilegeHandler),
    ('/authorize', AuthorizeHandler),
]
