#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..base.models import db, ModelMixin

# datanode table, which contain "show @@datanode" information
class DataNode(db.Model, ModelMixin):
    __tablename__ = "datanode"

    id              = db.Column(db.BigInteger, primary_key=True)
    name            = db.Column(db.String(64), nullable=True)
    datasource      = db.Column(db.String(128), nullable=True)
    index           = db.Column(db.Integer, nullable=True)
    cobar_ip        = db.Column(db.String(64), nullable=True)
    cobar_user_port = db.Column(db.Integer, nullable=True)
    cobar_adm_port  = db.Column(db.Integer, nullable=True)
    cluster         = db.Column(db.String(16), nullable=False)
    last_change     = db.Column(db.DateTime, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('cobar_ip','datasource','cobar_adm_port', name='idx_uni_key'),
        )

# datasource table, which contain "show @@datasource" information
class DataSource(db.Model, ModelMixin):
    __tablename__ = "datasource"

    id              = db.Column(db.BigInteger, primary_key=True,autoincrement=True)
    name            = db.Column(db.String(64), nullable=True)
    host            = db.Column(db.String(64), nullable=True)
    port            = db.Column(db.Integer, nullable=True)
    schema          = db.Column(db.String(64), nullable=True)
    cobar_ip        = db.Column(db.String(64), nullable=True)
    cobar_user_port = db.Column(db.Integer, nullable=True)
    cobar_adm_port  = db.Column(db.Integer, nullable=True)
    cluster         = db.Column(db.String(16), nullable=False)
    last_change     = db.Column(db.DateTime, nullable=False)

    __table_args__ = (
        #db.PrimaryKeyConstraint('cobar_ip','name','cobar_adm_port'),
        db.UniqueConstraint('cobar_ip','name','cobar_adm_port',name='idx_uni_cobar'),
        #db.Index('cobar_ip','cobar_user_port',name='index_cobar'),
        )

# database table, which contain pa<->schema relation ship
class DataBase(db.Model, ModelMixin):
    __tablename__ = "database"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    pa = db.Column(db.String(64), nullable=True)
    schema = db.Column(db.String(64), nullable=True)


# server table, which contain cobar "show @@server" information
class Server(db.Model, ModelMixin):
    __tablename__ = "cobar_server"

    id              = db.Column(db.BigInteger, primary_key=True,autoincrement=True)
    cobar_ip        = db.Column(db.String(64), nullable=False)
    cluster         = db.Column(db.String(16), nullable=True)
    cobar_adm_port  = db.Column(db.Integer, nullable=False)
    uptime          = db.Column(db.String(64), nullable=True)
    used_memory     = db.Column(db.BigInteger, nullable=True)
    total_memory    = db.Column(db.BigInteger, nullable=True)
    max_memory      = db.Column(db.BigInteger, nullable=True)
    reload_time     = db.Column(db.BigInteger, nullable=True)
    rollback_time   = db.Column(db.BigInteger, nullable=True)
    charset         = db.Column(db.String(16), nullable=True)
    status          = db.Column(db.String(16),nullable=True)
    last_change     = db.Column(db.DateTime, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('cobar_ip','cobar_adm_port',name='idx_uni_cobar'),
        )

# server table, which contain cobar "show @@server" information
class MySQLInstances(db.Model, ModelMixin):
    __tablename__ = "mysql_instances"

    host            = db.Column(db.String(64), nullable=True)
    ip              = db.Column(db.String(15), nullable=False)
    port            = db.Column(db.Integer, nullable=False)
    datadir         = db.Column(db.String(128), nullable=True)
    user            = db.Column(db.String(64), nullable=True)
    version         = db.Column(db.String(32), nullable=True)
    masterhost      = db.Column(db.String(64), nullable=True)
    masterip        = db.Column(db.String(15), nullable=True)
    masterport      = db.Column(db.Integer, nullable=True)
    slaves          = db.Column(db.String(1024), nullable=True)
    dbs             = db.Column(db.String(1024), nullable=True)
    last_change     = db.Column(db.DateTime, nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('ip','port'),
        )

# userauth table, which contain user relation ship with schema
# this table is using for offline view data authentication
class UserAuth(db.Model, ModelMixin):
    __tablename__ = "userauth"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username    = db.Column(db.String(64),nullable=False)
    schema      = db.Column(db.String(64),nullable=False)
    expire_time = db.Column(db.DateTime, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)
