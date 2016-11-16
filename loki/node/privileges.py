# coding=utf-8
from ..base.privileges import PrivilegeBase, PrivilegeItem, PrivilegeGroup


class NodePrivilege(PrivilegeBase):
    __type__ = PrivilegeGroup.critical
    __privileges__ = (
        PrivilegeItem('admin', u'管理 node 权限的分配'),
        PrivilegeItem('create_node', u'创建节点'),
        PrivilegeItem('manage_node', u'进行节点管理操作，包含移动、改名、删除'),
        PrivilegeItem('manage_node_relatives', u'管理与节点相关联的属性，包含节点上的机器和域名'),
    )
    __privilege_name__ = 'node'
    __privilege_alias__ = '节点'
