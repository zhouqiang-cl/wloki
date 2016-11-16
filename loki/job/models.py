#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from loki.utils.sqlalchemy_custom_type import JSONObject

from ..app import settings
from ..utils import catch_exception
from ..base.models import db, ModelMixin
from ..signals import deploy as deploy_signal


logger = logging.getLogger("job.models")


class Package(db.Model, ModelMixin):
    __tablename__ = "packages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), index=True, nullable=False)
    target_filename = db.Column(db.String(50), nullable=False)
    branch = db.Column(db.String(50), index=True, nullable=False)
    idc = db.Column(db.String(50), nullable=False)
    ctime = db.Column(db.DateTime, nullable=False)
    url = db.Column(db.String(300), nullable=False)
    md5 = db.Column(db.String(50), nullable=False)


class Template(db.Model, ModelMixin):
    __tablename__ = "template"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    node_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    parameters = db.Column(JSONObject(db.Text(500)), nullable=False)
    ctime = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    mtime = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('name', 'node_id', name='template_unique_index'),)


class Deployment(db.Model, ModelMixin):
    __tablename__ = "deployment"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    node_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    parameters = db.Column(JSONObject(db.Text(500)), nullable=False)
    ctime = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    mtime = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)
    status = db.Column(db.Integer, nullable=False)

    @classmethod
    @catch_exception(logger)
    def set_status(cls, _id, status):
        try:
            d = Deployment.query.with_for_update().get(_id)
            if d is not None and d.status != int(status):
                d.status = int(status)
                d.save()
                deploy_signal.on_status_changed.send(d)
        finally:
            db.session.rollback()
