# coding=utf-8
from ..base.privileges import PrivilegeBase, PrivilegeItem, PrivilegeGroup


class JobPrivilege(PrivilegeBase):
    __type__ = PrivilegeGroup.normal
    __privileges__ = (
        PrivilegeItem('admin', u'管理 job 权限的分配'),
        PrivilegeItem('manage_template', u'管理模板 (CRUD)'),
        PrivilegeItem('manage_deployment', u'管理任务部署 (CRUD)'),
    )
    __privilege_name__ = 'job'
    __privilege_alias__ = '发布'
