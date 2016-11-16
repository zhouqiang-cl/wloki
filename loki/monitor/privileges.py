# coding=utf-8
from ..base.privileges import PrivilegeBase, PrivilegeItem, PrivilegeGroup


class MonitorRelativesPrivilege(PrivilegeBase):
    __type__ = PrivilegeGroup.normal
    __privileges__ = (
        PrivilegeItem('admin', u'管理 monitor_relatives 权限的分配'),
        PrivilegeItem('manage_relatives', u'管理模板关联 (CRUD)'),
    )
    __privilege_name__ = 'monitor_relatives'
    __privilege_alias__ = '监控关联'


# class MonitorTemplatesPrivilege(PrivilegeBase):
#     __type__ = PrivilegeGroup.normal
#     __privileges__ = (
#         PrivilegeItem('admin', u'管理 monitor_templates 权限的分配'),
#         PrivilegeItem('manage_templates', u'管理模板 (CRUD)'),
#     )
#     __privilege_name__ = 'monitor_templates'
#     __privilege_alias__ = '监控模板'
