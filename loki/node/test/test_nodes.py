from gevent import monkey
monkey.patch_all()
from unittest import TestCase
from loki.node.nodes import TreeNode


class TreeNodeTest(TestCase):
    def test_bfs_generator(self):
        node = TreeNode(1, with_path=True)
        for n in node.bfs_generator():
            print n

    def test_dfs_generator(self):
        node = TreeNode(1, with_path=True)
        for n in node.dfs_generator():
            print n
