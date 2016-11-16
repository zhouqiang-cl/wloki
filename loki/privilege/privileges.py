# coding=utf-8
from ..base.privileges import PrivilegeBase, PrivilegeItem, PrivilegeGroup


class GrantingPrivilege(PrivilegeBase):
    __type__ = PrivilegeGroup.critical
    __privileges__ = (
        PrivilegeItem('admin', u'管理 granting 权限的分配'),
        PrivilegeItem('grant_normal_privileges', u'赋予 cdn, redis, server, job, asset 的 admin 权限'),
        PrivilegeItem('grant_critical_privileges', u'赋予 node, granting 的 admin 权限'),
    )
    __privilege_name__ = 'granting'
    __privilege_alias__ = '权限分配'
