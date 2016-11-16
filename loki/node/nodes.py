# -*- coding: utf-8 -*-
from enum import Enum
from functools import wraps
from collections import defaultdict
from loki.node.models import NodeServers
from loki.zookeeper import zk, NoNodeError
from logging import getLogger
import traceback

logger = getLogger("loki.node.TreeNode")


class NodeType(Enum):
    leaf = 1
    node = 2


class _Context(object):
    pass


def memorize(fn):
    @wraps(fn)
    def decorator(self, *args, **kwargs):
        memorized_key = "memorize_%s" % fn.__name__
        if memorized_key not in self.__memorize__:
            self.__memorize__.update({memorized_key: fn(self, *args, **kwargs)})
        return self.__memorize__[memorized_key]
    return decorator


class TreeNode(object):
    __slots__ = ("id", "name", "parent", "_servers",
                 "path", "with_path", "_context", "__memorize__")

    def __new__(cls, node_id, _context=None, *args, **kwargs):
        if _context is None:
            _context = _Context()

        if not hasattr(_context, "tree_nodes"):
            _context.tree_nodes = {}

        node = _context.tree_nodes.get(node_id)
        if node is None:
            node = super(TreeNode, cls).__new__(cls, node_id, _context, *args, **kwargs)
            node._context = _context
            node.__memorize__ = {}
            _context.tree_nodes[node_id] = node
        return node

    def __init__(self,
                 node_id,
                 _context=None,
                 with_path=False):
        try:
            # TODO: remove with_path argument
            if not isinstance(node_id, int):
                node_id = int(node_id)
            node = self.node_dict[node_id]
            self.with_path = with_path
            assert node_id == node['id']
            self.id = node['id']
            self.parent = node['pId']
            self.name = node['name']
        except KeyError as e:
            traceback.print_exc()
            raise NoNodeError("no node error: %s" % str(e))

    def dfs_generator(self):
        """
        depth first search
        :rtype: collections.Iterable[TreeNode]
        """
        yield self
        for _node in self.children:
            for __node in TreeNode.dfs_generator(_node):
                yield __node

    def bfs_generator(self):
        """
        breadth first search
        :rtype: collections.Iterable[TreeNode]
        """
        for node in self._bfs_nodes([self]):
            yield node

    def _bfs_nodes(self, nodes):
        """
        breadth first search
        :type nodes: collections.Iterable[TreeNode]
        :rtype: collections.Iterable[TreeNode]
        """
        new_nodes = []
        for node in nodes:
            yield node
            new_nodes.extend(node.children)
        if new_nodes:
            for node in self._bfs_nodes(new_nodes):
                yield node

    @property
    @memorize
    def path(self):
        return self.node_dirs[self.id]

    @property
    @memorize
    def level(self):
        return self.path.count('/')

    @property
    @memorize
    def height(self):
        children_levels = [child.level for child in self.dfs_generator()]
        if not len(children_levels):
            return 0
        else:
            return max(children_levels) - self.level

    @property
    @memorize
    def offspring_treenode(self):
        """
        :rtype: collections.Iterable[TreeNode]
        """
        return list(self.dfs_generator())

    @property
    @memorize
    def offspring_nodeservers(self):
        return NodeServers.get_by_node_ids([n.id for n in self.offspring_treenode
                                            if n.type is NodeType.leaf])

    @property
    @memorize
    def type(self):
        if len(self.children) == 0:
            return NodeType.leaf
        else:
            return NodeType.node

    @property
    @memorize
    def nodeservers(self):
        """
        breadth first search
        :rtype: collections.Iterable[NodeServers]
        """
        if self.type is NodeType.node:
            return ()
        nodes = NodeServers.get_by_node_id(node_id=self.id)
        return nodes

    @property
    @memorize
    def servers(self):
        return (_node.server for _node in self.nodeservers)

    @property
    @memorize
    def online_servers(self):
        if self.type is NodeType.node:
            return ()
        nodes = NodeServers.get_by_node_id(node_id=self.id, exclude_offline=True)
        return (_node.server for _node in nodes)

    @property
    def node_dirs(self):
        if not hasattr(self._context, "node_dirs"):
            node_dirs = self.get_tree_dirs()
            self._context.node_dirs = node_dirs
        return self._context.node_dirs

    @property
    def children_map(self):
        if not hasattr(self._context, "children_map"):
            node_dict, children_map = self.get_tree_meta()
            self._context.node_dict = node_dict
            self._context.children_map = children_map
        return self._context.children_map

    @property
    def node_dict(self):
        if not hasattr(self._context, "node_dict"):
            node_dict, children_map = self.get_tree_meta()
            self._context.node_dict = node_dict
            self._context.children_map = children_map
        return self._context.node_dict

    @property
    def meta(self):
        if not hasattr(self._context, "meta"):
            logger.debug("get meta from zk")
            meta = zk.without_expire.get_meta()
            self._context.meta = meta
        return self._context.meta

    @property
    @memorize
    def children(self):
        return {TreeNode(child_id,
                         _context=self._context)
                for child_id in self.children_map[self.id]}

    @property
    def parents(self):
        if self.parent:
            parent = TreeNode(self.parent, _context=self._context)
            yield parent
            for i in parent.parents:
                yield i

    def get_tree_dirs(self):
        raw = self.meta['dirs']
        node_dirs = dict((v, k) for k, v in raw.items())
        return node_dirs

    def get_tree_meta(self):
        raw = self.meta['tree']
        d = {}
        children_map = defaultdict(list)
        for i in raw:
            d[i['id']] = dict(id=i['id'], pId=i['pId'], name=i['name'])
            children_map[i['pId']].append(i['id'])
        return d, children_map

    def __hash__(self):
        return hash(self.id)

    def __unicode__(self):
        return u'<TreeNode %s id: %d>' % (self.name, self.id)

    def __str__(self):
        return unicode(self).encode('utf8')
