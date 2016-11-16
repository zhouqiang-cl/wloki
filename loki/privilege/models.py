#!/usr/bin/env python
# -*- coding: utf-8 -*-
from itertools import chain

import enum
from sqlalchemy import Index
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import deferred, load_only, joinedload

from loki import errors
from loki.server.models import RawServer
from ..base.models import ModelMixin, db
from ..base.privileges import get_privilege_by_name
from ..node.nodes import TreeNode
from ..utils.sqlalchemy_custom_type import JSONObject


def authorize(privilege, username, node_id=None, hostname=None):
    """
    :type privilege: PrivilegeBase
    :type username: basestring
    :type node_id: int
    :type hostname: basestring
    """
    if not node_id:
        if not hostname:
            raise errors.ParamsInvalidError("must have parameter node_id or hostname")
        else:
            server = RawServer.query \
                .options(load_only(RawServer.id)) \
                .options(joinedload(RawServer.nodes).load_only("node_id")) \
                .filter_by(hostname=hostname).first_or_404()
            nodes = [TreeNode(node.node_id) for node in server.nodes]
    else:
        nodes = [TreeNode(node_id)]

    node_ids = {n.id for n in chain(*[tree_node.parents for tree_node in nodes])}
    node_ids |= {n.id for n in nodes}

    privilege_models = PrivilegeType.query \
        .options(load_only(PrivilegeType._matrix)) \
        .filter((PrivilegeType.node_id.in_(node_ids))) \
        .filter_by(privilege_type=privilege.name,
                   username=username) \
        .all()

    if not privilege_models:
        # raise errors.DoesNotExist('You have not applied for this type of privilege.')
        raise errors.HasNoPermission("Require {} privilege to access this resource, you havn't apply for it yet".format(privilege))

    if not any(p.has_privilege(privilege) for p in privilege_models):
        # raise errors.HasNoPermission("Privilege has not been applied for, is applying, is rejected or has been revoked.")
        raise errors.HasNoPermission("Require {} privilege to access this resource".format(privilege))


class PrivilegeStatus(enum.IntEnum):
    pending  = 0b0000
    applying = 0b0010
    approved = 0b0001
    rejected = 0b0100
    revoked  = 0b1000

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "<Status: %s>" % self.name

    def __unicode__(self):
        return str(self).decode("utf-8")

    def for_json(self):
        return repr(self)


class PrivilegeType(db.Model, ModelMixin):
    __tablename__ = "privileges"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    node_id = db.Column(db.Integer, nullable=False)
    privilege_type = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(30), nullable=True)
    _matrix = db.Column("matrix", db.BigInteger, default=0x0, nullable=False)
    extra_info = db.Column(JSONObject(db.String(300)), nullable=True)
    modifier = deferred(db.Column(db.String(30), nullable=True), group="audit")
    ctime = deferred(db.Column(db.DateTime, default=db.func.now(), nullable=False), group="audit")
    mtime = deferred(db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=True),
                     group="audit")

    __table_args__ = (Index('id', 'node_id', 'privilege_type', 'username', 'matrix', 'extra_info'),
                      Index('node_id', 'privilege_type', 'username', unique=True))

    def __init__(self, node_id, privilege_cls, username, extra_info=None):
        """
        :type node_id: int
        :type privilege_cls: loki.base.privileges.PrivilegeBase
        :type username: basestring
        :type extra_info: basestring | None
        """
        self.node_id = node_id
        self.privilege_type = privilege_cls.name
        self._matrix = privilege_cls.matrix
        self.username = username
        self.extra_info = extra_info

    @property
    def privileges(self):
        """
        :rtype : loki.base.privileges.PrivilegeBase
        """
        return get_privilege_by_name(self.privilege_type)(self._matrix)

    @privileges.setter
    def privileges(self, p):
        """
        :type p: loki.base.privileges.PrivilegeBase
        """
        self._matrix = p.matrix

    @hybrid_method
    def has_privilege(self, p):
        """
        :type p: loki.base.privileges.PrivilegeBase
        """
        return self._matrix & p.matrix != 0b0

    @has_privilege.expression
    def has_privilege(self, p):
        """
        :type p: loki.base.privileges.PrivilegeBase
        """
        return self._matrix.op('&')(p.matrix) != 0b0

    def for_json(self):
        privileges = self.privileges

        return {
            "id": self.id,
            'username': self.username,
            "node_id": self.node_id,
            'node_path': TreeNode(self.node_id, with_path=True).path,
            "privilege_type": self.privilege_type,
            "privileges": [
                {
                    "name": privilege_name,
                    "status": PrivilegeStatus(privileges.get_matrix_by_name(privilege_name)).name
                }
                for privilege_name in privileges.enum.__members__.keys()
            ],
            "ctime": self.ctime,
            "mtime": self.mtime,
        }
