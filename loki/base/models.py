#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..db import db
from sqlalchemy import distinct
from functools import wraps


def bind(func):
    @wraps(func)
    def wrapper(self, bind=None, *args, **kwargs):
        if bind is None:
            bind = db
        return func(self, bind, *args, **kwargs)
    return wrapper


def bind_static(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        _bind = kwargs.pop('bind', None)
        if _bind is None:
            _bind = db
        return func(_bind, *args, **kwargs)
    return wrapper


class ModelMixin(object):
    @bind
    def add(self, bind=None):
        bind.session.add(self)

    @bind
    def save(self, bind=None):
        try:
            bind.session.add(self)
            bind.session.commit()
            return self
        except Exception as e:
            bind.session.rollback()
            raise e

    @bind
    def remove(self, bind=None):
        bind.session.delete(self)

    @bind
    def delete(self, bind=None):
        try:
            bind.session.delete(self)
            return bind.session.commit()
        except Exception as e:
            bind.session.rollback()
            raise e

    def to_dict(self, *args):
        d = self.__dict__
        if args:
            return dict((k, getattr(self, k)) for k in args)
        else:
            return dict((k, d[k]) for k in d.iterkeys() if not k.startswith("_"))

    @staticmethod
    @bind_static
    def commit(bind=None):
        try:
            bind.session.commit()
        except Exception as e:
            bind.session.rollback()
            raise e

    @staticmethod
    @bind_static
    def distinct(bind=None, *args, **kwargs):
        return bind.session.query(distinct(*args, **kwargs))

    @staticmethod
    @bind_static
    def subquery(bind=None, *args, **kwargs):
        return bind.session.query(*args, **kwargs)

    @staticmethod
    @bind_static
    def flush(bind=None):
        try:
            bind.session.commit()
        except Exception:
            bind.session.rollback()

    @staticmethod
    @bind_static
    def rollback(bind=None):
        bind.session.rollback()
