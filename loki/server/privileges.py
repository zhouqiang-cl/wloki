# coding=utf-8
from ..base.privileges import PrivilegeBase, PrivilegeItem, PrivilegeGroup


class ServerPrivilege(PrivilegeBase):
    __type__ = PrivilegeGroup.normal
    __privileges__ = (
        PrivilegeItem('admin', u'管理 server 权限的分配'),
        PrivilegeItem('login', u'登录服务器'),
        PrivilegeItem('work', u'使用 work 用户'),
    )
    __privilege_name__ = 'server'
    __privilege_alias__ = '服务器登陆'
