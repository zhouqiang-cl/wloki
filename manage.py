#!/usr/bin/env python
# -*- coding: utf-8 -*-


import loki  # NOQA
from gevent import monkey
from torext.script import Manager


manager = Manager()


def setup_env():
    from loki.app import init_app
    init_app()


def apply_extra_settings(app, kwargs):
    if 'LOGGING_DEBUG' in kwargs:
        flag = kwargs.pop('LOGGING_DEBUG')
        if flag:
            kwargs['LOGGERS'] = dict(app.settings['LOGGERS'])
            kwargs['LOGGERS']['']['level'] = 'DEBUG'

    if 'PRODUCTION' in kwargs:
        del kwargs['PRODUCTION']
        kwargs['STATIC_PATH'] = '../build/static'
        kwargs['TEMPLATE_PATH'] = '../build/template'

    app.update_settings(kwargs, convert_type=True, log_changes=True)


@manager.command(profile=True)
@manager.prepare(setup_env)
def sync_with_zk(idc_id=None):
    from loki.sync import sync_servers_zk
    sync_servers_zk(idc_id)


@manager.command()
@manager.prepare(setup_env)
def sync_with_assets(interval=600, test=False):
    from loki.sync import SyncAssetsDaemon
    d = SyncAssetsDaemon(interval)
    d.run(test=test)


@manager.command()
@manager.prepare(setup_env)
def zk_servers_sync_run():
    from loki.sync import SyncServersDaemon
    deamon = SyncServersDaemon()
    deamon.run()


@manager.command()
@manager.prepare(setup_env)
def init_servers(username, password):
    print "this function has been abandoned"


@manager.command()
@manager.prepare(setup_env)
def syncdb(**kwargs):
    from loki.db import db
    db.create_all()
    return


@manager.command()
@manager.prepare(setup_env)
def dropdb(**kwargs):
    from loki.db import db
    db.drop_all()
    return


@manager.command()
@manager.prepare(setup_env)
def show_create_table(model):
    from importlib import import_module
    from loki.db import db
    from sqlalchemy.schema import CreateTable
    module_name, class_name = model.rsplit(".", 1)
    module = import_module(module_name)
    _class = getattr(module, class_name)
    print CreateTable(_class.__table__).compile(bind=db._engine)


@manager.command()
def gevent_run(**kwargs):
    """Use gevent to run server in WSGI mode, arguments are the same as `run`
    command
    """
    print "Please use uwsgi mode to run this application, check Makefile for more infomation"


@manager.command()
def appoint_superuser(username):
    """Grant admin of all types of privileges for a user.

    A superuser basically has all granting privileges, but for convenience,
    each type's admin privilege should be granted for the user
    """
    from loki.privilege.models import PrivilegeStatus, PrivilegeType
    from loki.privilege.privileges import GrantingPrivilege
    from loki.base.privileges import get_all_privileges_items

    # Set granting
    privilege = GrantingPrivilege()
    privilege.set_matrix_by_name('grant_normal_privileges', PrivilegeStatus.approved)
    privilege.set_matrix_by_name('grant_critical_privileges', PrivilegeStatus.approved)
    privilege.set_matrix_by_name('admin', PrivilegeStatus.approved)
    privilege_model = PrivilegeType(node_id=1,
                                    username=username,
                                    privilege_cls=privilege)
    privilege_model.save()

    # Set others
    for name, privilege_type_cls in get_all_privileges_items():
        if name == 'granting':
            continue
        print '##', name, privilege_type_cls
        privilege = privilege_type_cls()
        privilege.set_matrix_by_name('admin', PrivilegeStatus.approved)
        privilege_model = PrivilegeType(node_id=1,
                                        username=username,
                                        privilege_cls=privilege)
        privilege_model.save()


@manager.command()
def clear_privileges():
    from loki.privilege.models import PrivilegeType

    PrivilegeType.query.delete()


if "__main__" == __name__:
    manager.run()
