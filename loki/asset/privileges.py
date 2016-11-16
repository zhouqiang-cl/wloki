# coding=utf-8
from ..base.privileges import PrivilegeBase, PrivilegeItem, PrivilegeGroup


class AssetPrivilege(PrivilegeBase):
    __type__ = PrivilegeGroup.normal
    __privileges__ = (
        PrivilegeItem('admin', u'管理 asset 权限的分配'),
        PrivilegeItem('manage_asset', u'管理资产条目'),
    )
    __privilege_name__ = 'asset'
    __privilege_alias__ = '资产'
