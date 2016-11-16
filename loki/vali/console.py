# coding: utf-8

__author__ = "qinguoan@nosa.me"

import os
import sys
import argparse
import ujson as json
from loki.zookeeper import zk
from inspect import getdoc, getframeinfo, currentframe


def create_parser(func, argument):
    usage = getdoc(func)
    parser = argparse.ArgumentParser(usage='%(prog)s ' + usage)
    if not argument:
        parser.print_help()
        exit(1)
    return parser


def get_node_tree(data, result=list(), count=0):
    for k, v in data.iteritems():
        name = zk.get_node_name(k)
        if not name:
            return "get node name error:", k
        name = "%s" % name
        indent = "│   " * count
        name = name.encode()
        output = "%s├── %s" % (indent, name)
        result.append(output)
        if isinstance(v, dict):
            # 如果一直有一下层就一直递归获取key。
            count += 1
            get_node_tree(v, result, count)
            # 只有当到了最后一层get_node_tree才能正常退回上一层循环。
            # 这时候需要将层数减去1才能是上一层的层号。
            result[-1] = result[-1].replace('├──', '└──')
            count -= 1
        else:
            continue

    return result


class ConsoleCommand(object):

    def __init__(self, argument):
        self.argument = argument

    def run(self):
        """
        <command>

        command:
          node       operations about tree.
          server     opetations about server.
          service    operations about service.
          job        operations about jobs.
          procedure  operations about job procedures.
          template   operations about script templates.
          zookeeper  operations about zookeeper itself.
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('command')
        args = parser.parse_args([self.argument.pop(0)])

        if not hasattr(self, args.command):
            parser.print_help()
            exit(1)

        return getattr(self, args.command)()

    def node(self):
        """
        node <command>

        command:
          get-node   show total tree structure or specified node's structure.
          add-node   add node onto current tree nodes.
          move-node  change parent node of an exist node.
          del-node   delete exist node from the tree.
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('command')
        args = parser.parse_args([self.argument.pop(0)])
        func = args.command.replace('-', '_')

        if not hasattr(self, func):
            parser.print_help()
            exit(1)

        return getattr(self, func)()

    def get_node(self):
        """
        node get-node <command> [options]

        command:
          --node-path  specified path for which to show subscribe
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-path', help='path of node', required=True)
        args = parser.parse_args(self.argument)
        tree_meta = zk.get_tree_meta()

        if tree_meta:
            if args.node_path != '/':
                dir_meta = zk.get_dirs_meta()
                if args.node_path not in dir_meta:
                    return False
                else:
                    node = dir_meta[args.node_path]
                ret = zk.tree_node_sub(tree_meta, node)
            else:
                ret = zk.tree_node_sub(tree_meta)

            return "\n".join(get_node_tree(ret)) if ret else None

        return None

    def add_node(self):
        """
        node add-node <command> [options]

        command:
          --node-id    id of new node
          --node-pid   pid of new node
          --node-name  name of new node
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='node id', type=int)
        parser.add_argument('--node-pid', required=True,
                            help='node pid', type=int)
        parser.add_argument('--node-name', required=True,
                            help='node name', type=str)
        args = parser.parse_args(self.argument)
        node = {"id": args.node_id, "pId": args.node_pid,
                "name": args.node_name}

        return zk.add_tree_node(node)

    def del_node(self):
        """
        node del-node <command> [options]

        command:
          --node-path  specified path for which to delete
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-path', help='path of node', type=str)
        args = parser.parse_args(self.argument)
        dir_meta = zk.get_dirs_meta()
        if args.node_path not in dir_meta:

            return False

        else:
            node = dir_meta[args.node_path]

            return zk.del_tree_node(node)

    def move_node(self):
        """
        node move-node <command> [options]

        command:
          --node-id  node id of node
          --dst-pid  which pid to change to.
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='source node id', type=int)
        parser.add_argument('--dst-pid', required=True,
                            help='new node pid', type=int)
        args = parser.parse_args(self.argument)
        name = zk.get_node_name(args.node_id)
        node = {"id": args.node_id, "pId": args.dst_pid, "name": name}

        return zk.move_tree_node(node)

    def server(self):
        """
        server <command>

        command:
          get-server  list all servers of specified node
          del-server  delete server from specified node
          add-server  add server to specified node
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('command')
        args = parser.parse_args([self.argument.pop(0)])
        func = args.command.replace('-', '_')

        if not hasattr(self, func):
            parser.print_help()
            exit(1)

        return getattr(self, func)()

    def get_server(self):
        """
        server get-server <command> [options]

        command:
          --node-id      node id of node
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='source node id', type=int)
        args = parser.parse_args(self.argument)
        ret = zk.get_total_servers(args.node_id, recursive=True)

        return "\n".join(ret) if isinstance(ret, list) else ret

    def del_server(self):
        """
        server del-server <command> [options]

        command:
          --node-id  node id of node
          --server-name  which server to delete
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='source node id', type=int)
        parser.add_argument('--server-name', nargs='*', required=True,
                            help='source node id', type=str)
        args = parser.parse_args(self.argument)

        return zk.del_node_servers(args.node_id, *args.server_name)

    def add_server(self):
        """
        server add-server <command> [options]

        command:
          --node-id         node id of node
          --server-name     which server to delete
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='source node id', type=int)
        parser.add_argument('--server-name', nargs='*', required=True,
                            help='source node id', type=str)
        args = parser.parse_args(self.argument)

        return zk.add_node_servers(args.node_id, *args.server_name)

    def service(self):
        """
        service <command>

        command:
          get-service-desc    get service description
          add-service-desc    inital service description
          set-service-type    set node type
          get-service-type    get node type
          set-service-above   set service above dependence
          get-service-above   get service above dependence
          set-service-below   set service below dependence
          get-service-below   get service below dependence
          set-service-attr    set service attr key
          get-service-attr    get service attr key
          del-service-attr    del service attr key
          set-service-env     update service env
          set-env-name        service env rename
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('command')
        args = parser.parse_args([self.argument.pop(0)])
        func = args.command.replace('-', '_')

        if not hasattr(self, func):
            parser.print_help()
            exit(1)

        return getattr(self, func)()

    def get_service_desc(self):
        """
        service get-service-desc <command> [options]

        command:
          --node-id    node id of node
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='source node id', type=int)
        args = parser.parse_args(self.argument)

        return zk.get_service_desc(args.node_id)

    def add_service_desc(self):
        """
        service add-service-desc <command> [options]

        command:
          --node-id    node id of node
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='source node id', type=int)
        args = parser.parse_args(self.argument)

        return zk.add_service_desc(args.node_id)

    def set_service_type(self):
        """
        service set-service-type <command> [options]

        command:
          --node-id    node id of node
          --node-type    new type of service node.
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='source node id', type=int)
        parser.add_argument('--node-type', required=True,
                            help='source node id', type=str)
        args = parser.parse_args(self.argument)

        return zk.set_node_type(args.node_id, args.node_type)

    def get_service_type(self):
        """
        service get-service-type <command> [options]

        command:
          --node-id    node id of node
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='source node id', type=int)
        args = parser.parse_args(self.argument)

        return zk.get_node_type(args.node_id)

    def set_service_above(self):
        """
        service set-service-above <command> [options]

        command:
          --node-id    node id of node
          --above-node-id     dependence node id
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='source node id', type=int)
        parser.add_argument('--above-node-id', required=True,
                            help='above node id', type=int)
        args = parser.parse_args(self.argument)

        return zk.set_service_above_dep(args.node_id, args.above_node_id)

    def get_service_above(self):
        """
        service get-service-above <command> [options]

        command:
          --node-id    node id of node
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True, help='source node id',
                            type=int)
        args = parser.parse_args(self.argument)

        return zk.get_service_above_dep(args.node_id)

    def set_service_below(self):
        """
        service set-service-below <command> [options]

        command:
          --node-id    node id of node
          --above-node-id     dependence node id
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='source node id', type=int)
        parser.add_argument('--below-node-id', required=True,
                            help='below node id', type=int)
        args = parser.parse_args(self.argument)

        return zk.set_service_below_dep(args.node_id, args.above_node_id)

    def get_service_below(self):
        """
        service get-service-above <command> [options]

        command:
          --node-id    node id of node
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='source node id', type=int)
        args = parser.parse_args(self.argument)

        return zk.get_service_below_dep(args.node_id)

    def del_service_env(self):
        """
        servuce del-service-attr <command> [options]

        command:
          --node-id
          --env-name
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='node id', type=int)
        parser.add_argument('--env-name', required=True,
                            help='env name', type=str)
        args = parser.parse_args(self.argument)

        return zk.del_service_env(args.node_id, args.env_name)

    def set_service_env(self):
        """
        servuce set-service-attr <command> [options]

        command:
          --node-id
          --env-name
          --env-setup
          --env-test
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='node id', type=int)
        parser.add_argument('--env-name', required=True,
                            help='env name', type=str)
        parser.add_argument('--env-setup', required=True,
                            help='env setup command', type=str)
        parser.add_argument('--env-test', required=True,
                            help='env test command', type=str)
        args = parser.parse_args(self.argument)
        data = json.dumps({'name': args.env_name, 'setup': args.env_setup,
                           'test': args.env_test})

        return zk.add_service_env(args.node_id, data)

    def set_env_name(self):
        """
        servuce set-service-attr <command> [options]

        command:
          --node-id
          --old-name
          --new-name
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('--node-id', required=True,
                            help='node id', type=int)
        parser.add_argument('--old-name', required=True,
                            help='old env name', type=str)
        parser.add_argument('--new-name', required=True,
                            help='new env name', type=str)
        args = parser.parse_args(self.argument)

        return zk.set_service_env_name(args.node_id, args.old_name,
                                       args.new_name)

    def job(self):
        """
        job <command>

        command:
          get-job
          pause-job
          delete-job
          retry-job
          get-job-detail
          get-job-status
          get-job-logs
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('command')
        args = parser.parse_args([self.argument.pop(0)])
        func = args.command.replace('-', '_')

        if not hasattr(self, func):
            parser.print_help()
            exit(1)

        return getattr(self, func)()

    def set_job(self):
        """
        set-job <command>

        command:
          --node-id
          --procedure-id
        """
        parser = create_parser(getattr(self,
                               getframeinfo(currentframe()).function),
                               self.argument)
        parser.add_argument('command')
        parser.add_argument('--node-id', required=True,
                            help='node id', type=int)
        parser.add_argument('--procedure-id', required=True,
                            help='procedure name', type=str)
        args = parser.parse_args(self.argument)
