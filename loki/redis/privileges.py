# coding=utf-8
from ..base.privileges import PrivilegeBase, PrivilegeItem, PrivilegeGroup


class RedisPrivilege(PrivilegeBase):
    __type__ = PrivilegeGroup.critical
    __privileges__ = (
        PrivilegeItem('admin', u'管理 redis 权限的分配'),
        PrivilegeItem('manage_redis', u'进行 redis 管理操作'),
    )
    __privilege_name__ = 'redis'
    __privilege_alias__ = 'Redis'
