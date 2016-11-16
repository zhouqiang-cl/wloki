# coding=utf-8
from ..base.privileges import PrivilegeBase, PrivilegeItem, PrivilegeGroup


class CDNPrivilege(PrivilegeBase):
    __type__ = PrivilegeGroup.normal
    __privileges__ = (
        PrivilegeItem('admin', u'管理 CDN 权限的分配'),
        PrivilegeItem('view_cdn', u'查看 CDN 信息'),
        PrivilegeItem('manage_cdn', u'进行 CDN 管理操作'),
    )
    __privilege_name__ = 'cdn'
    __privilege_alias__ = 'CDN'
