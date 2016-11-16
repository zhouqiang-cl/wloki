#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..base.models import db, ModelMixin


class Domain(db.Model, ModelMixin):
    __tablename__ = "domains"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
