# coding: utf-8
from contextlib import contextmanager

__author__ = 'qinguoan@nosa.me'

from os import path
import socket
import ujson as json
from time import strftime, localtime

from kazoo.retry import KazooRetry
from kazoo.exceptions import KazooException, NoNodeError, BadVersionError
from kazoo.client import KazooState, KazooClient
from kazoo.handlers.gevent import SequentialGeventHandler
import gevent
from gevent import event

from loki.settings import ZK_ADDR
from loki.utils.lazy_init import lazy_init_with_lock

NODE = {
    "LOCK_PATH": "/loki/lock",
    "JOB_PATH": "/loki/job",
    "NEW_JOB_PATH": "/loki/job/new_job",
    "PENDING_JOB_PATH": "/loki/job/pending_job",
    "FINISH_JOB_PATH": "/loki/job/finish_job",
    "TEMPLATE_PATH": "/loki/template",
    "CONFIG_PATH": "/loki/configs",
    "AUDIT_PATH": "/loki/audit",
    "UNAPPROVED_PATH": "/loki/audit/unapproved",
    "APPROVED_PATH": "/loki/audit/approved",
    "TREE_PATH": "/loki/ptree",
}


class Node(object):
    def __init__(self, id, pId, name):
        if not isinstance(id, int):
            raise ArgumentError('id should be type int')
        if not isinstance(pId, int):
            raise ArgumentError('pid should be type int')
        if not isinstance(name, unicode):
            raise ArgumentError('name should be type unicode')
        self.id = id
        self.pId = pId
        self.name = name

    def to_dict(self):
        ret = {
            'id': self.id,
            'pId': self.pId,
            'name': self.name
        }
        return ret


class _BaseError(KazooException):
    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        if isinstance(self.msg, unicode):
            return self.msg.encode('utf8')
        return self.msg

    def __unicode__(self):
        if isinstance(self.msg, str):
            return self.msg.decode('utf8')
        return self.msg


class TimeoutError(_BaseError):
    pass


class ArgumentError(_BaseError):
    pass


class NodeValueError(_BaseError):
    pass


class ValueConflictError(_BaseError):
    pass


class NodeNotExistError(_BaseError):
    pass


class LockTimeoutError(_BaseError):
    pass


def get_node_sub_list(tree, result=None):
    if result is None:
        result = dict()
    bak = [x for x in tree]
    l = len(bak)
    for i in xrange(l):
        id, pid, name = int(bak[i]['id']), int(bak[i]['pId']), bak[i]['name']
        for j in xrange(i + 1, l):
            node = bak[j]
            tid, tpid, tname = int(node['id']), int(node['pId']), node['name']
            if id == tpid:
                tree = [x for x in tree if x['id'] != id]

    for i in tree:
        id, pid = i['id'], i['pId']
        if id not in result:
            result[id] = list()
        result[id].append(id)
        if pid not in result:
            result[pid] = list()
        result[pid] += result[id]

    if tree:
        new = [x for x in bak if x not in tree]
        get_node_sub_list(new, result)

    return result


def get_node_sub_dict(tree, result=None):
    if result is None:
        result = dict()
    bak = [x for x in tree]
    l = len(bak)
    for i in xrange(l):
        id, pid, name = int(bak[i]['id']), int(bak[i]['pId']), bak[i]['name']
        for j in xrange(i + 1, l):
            node = bak[j]
            tid, tpid, tname = int(node['id']), int(node['pId']), node['name']
            if id == tpid:
                tree = [x for x in tree if x['id'] != id]

    for i in tree:
        id, pid = i['id'], i['pId']
        if id not in result:
            result[id] = 1
        if pid not in result:
            result[pid] = dict()
        result[pid][id] = result[id]

    if tree:
        new = [x for x in bak if x not in tree]
        get_node_sub_dict(new, result)

    return result


def tree_node_map(tree_list):
    def get_node_path(node_id):
        if node_id == 0:
            return "/"
        name = tree_dict[node_id]['name']
        pid = tree_dict[node_id]['pId']
        return path.join(get_node_path(pid), name)
    data = {}
    tree_dict = dict((_n['id'], _n) for _n in tree_list)
    for _id in tree_dict.keys():
        data[get_node_path(_id)] = _id
    return data


class ZKClient(KazooClient):
    def __init__(self, host='127.0.0.1:2181', handler=None, ignore_expire=False):

        if handler == 'gevent':
            import gevent

            kr = KazooRetry(max_tries=-1,
                            delay=0.2,
                            sleep_func=gevent.sleep,
                            ignore_expire=ignore_expire)
            KazooClient.__init__(self,
                                 hosts=host,
                                 connection_retry=kr,
                                 handler=SequentialGeventHandler())
        else:
            kr = KazooRetry(max_tries=-1,
                            delay=0.2,
                            ignore_expire=ignore_expire)
            KazooClient.__init__(self,
                                 hosts=host,
                                 connection_retry=kr, )

        self.start()
        self.add_listener(self._conn_state_listener)

    @contextmanager
    def lock(self, path, block=True, timeout=None):
        path = NODE['LOCK_PATH'] + path

        if not self.exists(path):
            self.ensure_path(path)

        lock = self.Lock(path)
        lock.acquire(blocking=block, timeout=timeout)
        try:
            yield
        finally:
            lock.release()

    def semaphore(self, path, block=True, timeout=None, leases=1):
        path = NODE['LOCK_PATH'] + path

        if not self.exists(path):
            self.ensure_path(path)
        semaphore = self.Semaphore(path, max_leases=leases)
        semaphore.acquire(blocking=block, timeout=timeout)

        return semaphore

    def _conn_state_listener(self, state):
        if state == KazooState.LOST:
            print "connection and session expired"
        elif state == KazooState.SUSPENDED:
            print "connection lost, session unexpired"
        else:
            print "connection status ok"

    def get_node_dict(self, path):
        """
        get znode value.

        :param path: a zookeeper path, need exist or operation will be failed.

        :result type: return Faile if operation failed
        """
        meta, stats = self.get(path)

        try:
            meta = json.loads(meta)
        except Exception:
            raise NodeValueError("node value must be a json")

        return meta

    def set_node_dict(self, path, data, transaction=None):
        """
        set znode value.

        :param path: a zookeeper path, need exist or operation will be failed.
        :param data: data set to the specified node, a json from dict
        or a pure json.

        :result type: return Faile if operation failed
        """
        if isinstance(data, str):
            try:
                json.loads(data)
            except Exception:
                raise ArgumentError("argument string must be a json")
        elif isinstance(data, dict):
            data = json.dumps(data)
        else:
            raise ArgumentError("argument object must be a dict")

        if transaction is not None:
            return transaction.set_data(path, data)
        return self.set(path, data)

    def create_new_tree(self, tree):
        """
        create a new tree.

        :param tree: a json from list or a pure json, fit for zTree.

        :result type: return Faile if operation failed
        """
        tree_meta = dict()
        if isinstance(tree, str):
            try:
                tree = json.loads(tree)
            except Exception:
                raise ArgumentError("string must be a json")

        if not isinstance(tree, list):
            raise ArgumentError("object must be a list")

        tree_path = NODE['TREE_PATH']
        tree_meta['tree'] = tree
        tree_meta['dirs'] = tree_node_map(tree)

        with self.lock(tree_path, timeout=3):
            ret = self.set_node_dict(tree_path, tree_meta)

        for node in tree:
            path = self.get_node_path(node['id'])
            if not self.exists(path):
                self.create(path, json.dumps(node))
            else:
                self.set_node_dict(path, node)

        return ret

    def get_meta(self, name=None):
        tree_path = NODE['TREE_PATH']
        meta = self.get_node_dict(tree_path)
        if name is not None:
            return meta[name]
        else:
            return meta

    def get_dirs_meta(self):
        """
        get dirs data of tree.

        :param: None

        :reslut type: a dict object instance of :class:`result_ret`
        """
        return self.get_meta('dirs')

    def get_tree_meta(self):
        """
        get meta data of tree.

        :param: None

        :reslut type: a dict object instance of :class:`result_ret`
        """
        return self.get_meta('tree')

    def get_node_dir(self, node):
        """
        get node's dir.

        :param: nodeid

        :result type: a node string.
        """
        dirs = self.get_dirs_meta()
        dirs = dict((v, k) for k, v in dirs.items())
        dir = dirs.get(node, None)
        if not dir:
            raise NodeNotExistError("node %s not exist" % node)
        return dir

    def get_dir_node(self, path):
        dirs = self.get_dirs_meta()
        node = dirs.get(path, None)
        return node


    def get_next_id(self):
        """
        get next node of three

        :result type: int
        """
        tree = self.get_tree_meta()
        c = sorted(tree, key=lambda x: x['id'])
        return c[-1]['id'] + 1

    def add_tree_node(self, node):
        """
        add node to a exist tree.

        :param node: tree node meta data

        :return type: a dict object instance of :class:`result_ret`
        """
        nodes = self.get_node_children_names(node['pId'])
        if node['name'] in nodes:
            raise ValueConflictError("node %s belongs to pid %d already exists" % (node['name'], node['pId']))
        tree_path = NODE['TREE_PATH']
        with self.lock(tree_path, timeout=3):
            tree_meta = self.get_node_dict(tree_path)
            tree_meta['tree'].append(node)
            tree_meta['dirs'] = tree_node_map(tree_meta['tree'])
            self.set_node_dict(tree_path, tree_meta)
        path = self.get_node_path(node['id'])
        self.create(path)

        return self.set_node_dict(path, node)

    def move_tree_node(self, node_dict):
        """
        change pid of an exist id, also update tree meta.

        :param node_dict: tree node dict meta.

        :return type: a dict object instance of :class:`result_ret`
        """
        tree_path = NODE['TREE_PATH']
        node = Node(**node_dict)
        children = self.get_node_children_names(node.pId)
        if node.name in children:
            raise ValueConflictError('node %d already have child named %s' % (node.pId, node.name))
        with self.lock(tree_path, timeout=3):
            transaction = self.transaction()
            tree_meta = self.get_node_dict(tree_path)
            tree_meta['tree'] = [x for x in tree_meta['tree']
                                 if x['id'] != node.id]
            tree_meta['tree'].append(node.to_dict())
            tree_meta['dirs'] = tree_node_map(tree_meta['tree'])
            path = self.get_node_path(node.id)
            self.set_node_dict(tree_path, tree_meta, transaction)
            self.set_node_dict(path, node.to_dict(), transaction)
            transaction.commit()
        return True

    def del_tree_node(self, node):
        """
        delete an exist tree node

        :param node: tree node id

        :return type: a dict object instance of :class:`result_ret`
        """
        tree_path = NODE['TREE_PATH']
        with self.lock(tree_path, timeout=3):
            tree_meta = self.get_node_dict(tree_path)
            tree_meta['tree'] = [x for x in tree_meta['tree']
                                 if x['id'] != node]
            tree_meta['dirs'] = tree_node_map(tree_meta['tree'])
            self.set_node_dict(tree_path, tree_meta)
        path = self.get_node_path(node)

        return self.delete(path, recursive=True)

    def add_new_job(self, job):
        """
        create a new job which suffix with a autoincrement number

        :param job: meta of a new job, a json from dict or a pure json.

        :result type: return Faile if operation failed
        """
        if isinstance(job, str):
            try:
                node = json.loads(job)
            except Exception:
                raise ArgumentError("string must be a json")

        if not isinstance(node, dict):
            raise ArgumentError("object must be a dict")
        new_job_path = NODE['NEW_JOB_PATH']
        new_job_suffix = "%s/%s" % (new_job_path, "job")

        return self.create(new_job_suffix,
                           value=json.dumps(job), sequence=True, makepath=True)

    def get_node_servers(self, node):
        """
        get node and server map of an exist node, recursively.

        :param node: node id on the tree.

        :result type: return Faile if operation failed
        """
        tree_path = NODE['TREE_PATH']
        tree_meta = self.get_node_dict(tree_path)
        tree = tree_meta['tree']
        servers = dict()
        nodes = get_node_sub_list(tree)[node]
        for sub_node in nodes:
            server_path = "%s/%s/%s" % (tree_path, sub_node, "servers")
            try:
                children, _ = self.get(server_path)
            except NoNodeError:
                continue

            if children:
                servers[sub_node] = json.loads(children)

        return servers

    def get_total_servers(self, node, recursive):
        """
        get servers of an exist node, recursively or not

        :param node: node id on the tree.

        :result type: return Faile if operation failed
        """

        tree_path = NODE['TREE_PATH']
        if recursive:
            tree_meta = self.get_node_dict(tree_path)
            tree = tree_meta['tree']
            servers = set()
            nodes = get_node_sub_list(tree)[node]
            for sub_node in nodes:
                server_path = "%s/%s/%s" % (tree_path, sub_node, "servers")
                if not self.exists(server_path):
                    continue
                children, _ = self.get(server_path)
                if children:
                    servers = servers | set(json.loads(children))
        else:
            server_path = "%s/%s/%s" % (tree_path, node, "servers")
            try:
                servers, _ = self.get(server_path)
                if not servers:
                    servers = []
                else:
                    servers = json.loads(servers)
            except NoNodeError:
                servers = []

        if isinstance(servers, set):
            servers = list(servers)

        return servers

    def get_node_pid_async(self, node_id):
        def callback(greenlet):
            if greenlet.successful():
                result.set(greenlet.value)
            else:
                if isinstance(greenlet.exception, Exception):
                    result.set_exception(greenlet.exception)
                result.set_exception(NodeValueError("fetch node pid on node %s fail" % node_id))

        # tree_path = NODE['TREE_PATH']
        # path = "%s/%s" % (tree_path, node_id)
        result = event.AsyncResult()
        greenlet = gevent.spawn(self.get_node_pid, node_id)
        greenlet.link(callback)
        return result

    def get_node_pid(self, node_id):
        tree_path = NODE['TREE_PATH']
        path = "%s/%s" % (tree_path, node_id)

        try:
            data, _ = self.get(path)
        except NoNodeError:
            raise NodeNotExistError("node path %s not existed" % path)
        data = json.loads(data)
        return data["pId"]

    def get_node_parents_ids(self, node_id, cache=None):
        parents = []
        if cache and node_id in cache:
            pid = cache[node_id]
            if isinstance(pid, event.AsyncResult):
                pid = pid.get()
        else:
            pid = self.get_node_pid_async(node_id)
            if isinstance(cache, dict):
                cache[node_id] = pid
            pid = pid.get()
        assert pid is not None, "node_id %s's pid should not been None" % node_id

        parents.append(pid)
        if pid == 0:
            return parents
        else:
            parents = self.get_node_parents_ids(pid, cache=cache) + parents
            return parents

    def get_node_children_names(self, node_id, recursive=False):
        def callback(greenlet):
            ret.append(greenlet.value)

        if not isinstance(node_id, int):
            raise ArgumentError('node_id should be Type int')
        ret = []
        greenlets = []
        nodes = self.get_node_children(node_id, recursive=recursive)
        for _id in nodes:
            greenlet = gevent.spawn(self.get_node_name, _id)
            greenlet.link(callback)
            greenlets.append(greenlet)
        gevent.joinall(greenlets)
        return ret

    def get_node_children(self, node, recursive=False, tree=None, result=None):
        """
        """
        if not result:
            result = list()
            result.append(node)
        if not tree:
            tree = self.get_tree_meta()
        child = [x['id'] for x in tree if x['pId'] == node]
        if not recursive:
            return child
        if child:
            for i in child:
                result.append(i)
                self.get_node_children(i, recursive, tree, result)
        return result

    def tree_node_sub(self, tree, node=0):
        """
        return sub nodes of an exist node, recursively.

        :param tree: tree json list.
        :param node: node id on the tree.

        :result type: return Faile if operation failed
            subscribe nodes.
        """
        dirs = get_node_sub_dict(tree)

        return dirs[node]

    def get_node_name(self, node):
        """
        get node name of an exist node

        :param node: node id on the tree.

        :result type: return Faile if operation failed
        """
        path = self.get_node_path(node)
        meta = self.get_node_dict(path)

        return meta['name']

    def set_node_name(self, node, data):
        """
        set node name to an exist node

        :param node: node id on the tree.
        :param data: meta of the node, a json from dict or a json.

        :result type: return Faile if operation failed
        """
        path = self.get_node_path(node)
        with self.lock(path, timeout=3):
            meta = self.get_node_dict(node)
            meta['name'] = data

            return self.set_node_dict(path, meta)

    def init_new_job(self):
        """
        inital new job, move job from new_job to its node.
        add some schema for the job description.

        :param node: None

        :result type: return Faile if operation failed
        """
        tree_path = NODE['TREE_PATH']
        new_job_path = NODE['NEW_JOB_PATH']
        pending_path = NODE['PENDING_JOB_PATH']
        new_job_id = sorted(self.get_children(new_job_path))[0]
        new_job_node = "%s/%s" % (new_job_path, new_job_id)
        pending_node = "%s/%s" % (pending_path, new_job_id)
        new_job_meta, new_job_stats = self.get(new_job_node)
        try:
            new_job_meta = json.loads(new_job_meta)
        except Exception:
            raise NodeValueError("job meta must be a json")

        if not isinstance(new_job_meta, dict):
            raise NodeValueError("decoded from job meta must be a dict")

        node, procedure = new_job_meta['node_id'], new_job_meta['procedure_id']
        servers = self.get_node_servers(node)
        job_path = "%s/%s/%s/%s" % (tree_path, node, "jobs", new_job_id)
        job_meta = {
            "time": {"start": strftime("%F %T", localtime()), "STOP": None},
            "status": {
                "success": {},
                "running": {},
                "failure": {},
                "waiting": servers,
            },
            "tracker": socket.gethostname()
        }
        self.delete(new_job_node)
        self.create(pending_node, value=json.dumps(job_meta), makepath=True)
        self.create(job_path, value=json.dumps(job_meta), makepath=True)
        ret = list()
        for k, v in servers.items():
            for server in v:
                path = "%s/%s" % (job_path, server)
                stat = self.create(path, value="")
                ret.append(stat)

        return ret

    def get_job_node(node, job_id):
        """
        return zookeeper path of the specified job_id

        :param node: node id on the tree.
        :param job_id: an exist job of the node.

        :result type: return Faile if operation failed
        """

        return "%s/%s/%s/%s" % (NODE['TREE_PATH'], node, "jobs", job_id)

    def get_job_log(self, node, job_id, server):
        """
        get server log from an exist job of a specified node.

        :param node: node id on the tree.
        :param job_id: an exist job of the node.
        :param server: severs under the given node.

        :result type: return Faile if operation failed
        """
        server_path = self.get_job_node(node, job_id) + '/' + server
        meta = self.get_node_dict(server_path)

        return meta['log']

    def get_job_status(self, node, job_id):
        """
        get an exist job status of a specified node.

        :param node: node id on the tree.
        :param job_id: an exist job of the node.

        :result type: return Faile if operation failed
        """
        path = self.get_job_node(node, job_id)
        meta = self.get_node_dict(path)
        status = dict((k, dict((k1, len(v1)) for k1, v1 in v.items()))
                      for k, v in meta['status'].items())

        return status

    def get_job_detail(self, node, job_id):
        """
        get an exist job detail of a specified node.

        :param node: node id on the tree.
        :param job_id: an exist job of the node.

        :result type: return Faile if operation failed
        """
        path = self.get_job_node(node, job_id)
        meta = self.get_node_dict(path)

        return meta['status']

    @staticmethod
    def get_node_path(node):
        """
        get server log from an exist job of a specified node.

        :param node: node id on the tree.

        :result type: return Faile if operation failed
        """
        return "%s/%s" % (NODE['TREE_PATH'], node)

    def get_node_type(self, node):
        """
        get node type.

        :param node: node id on the tree.

        :result type: return Faile if operation failed
        """
        path = self.get_node_path(node)
        meta = self.get_node_dict(path)

        return meta['node_type'] if 'node_type' in meta else None

    def add_service_desc(self, node):
        """
        add description of an exist node.

        :param node: node id on the tree.

        :result type: return Faile if operation failed
        """
        meta = {
            "node_type": "service",
            "above_dependence": "",
            "below_dependence": "",
            "service_attr": {},
            "service_env": [],
        }
        path = self.get_node_path(node)

        return self.set_node_dict(path, meta)

    def set_service_desc(self, node, meta):
        """
        set description of an exist node.

        :param node: node id on the tree.
        :param meta: idescription meta data of the node

        :result type: return Faile if operation failed
        """
        path = self.get_node_path(node)

        return self.set_node_dict(path, meta)

    def get_service_desc(self, node):
        """
        get service description of an exist node.

        :param node: node id on the tree.

        :result type: return Faile if operation failed
        """
        path = self.get_node_path(node)
        meta = self.get_node_dict(path)

        return meta

    def fix_tree_meta(self):
        tree_path = NODE['TREE_PATH']
        children = self.get_children(tree_path)
        data = []
        for _id in children:
            n_path = path.join(tree_path, _id)
            value, _ = self.get(n_path)
            data.append(json.loads(value))
        with self.lock(tree_path, timeout=3):
            tree_meta = self.get_node_dict(tree_path)
            tree_meta['tree'] = data
            self.set_node_dict(tree_path, tree_meta)

    def fix_tree_dirs(self):
        tree_path = NODE['TREE_PATH']
        with self.lock(tree_path, timeout=3):
            tree_meta = self.get_node_dict(tree_path)
            data = tree_node_map(tree_meta['tree'])
            tree_meta['dirs'] = data
            self.set_node_dict(tree_path, tree_meta)

    def close(self):
        self.stop()

    @property
    def without_expire(zk):
        return zk_without_expire


# Use gevent as handler
zk = lazy_init_with_lock(ZKClient, ZK_ADDR, handler='gevent', ignore_expire=False)
zk_without_expire = lazy_init_with_lock(ZKClient, ZK_ADDR, handler='gevent', ignore_expire=True)

if __name__ == "__main__":

    #import gevent
    # zk = ZKClient(ZOO_ADDR, handler='gevent')
    # tree = zk.get_tree_meta()
    # sem = zk.Semaphore('/loki/lock/test')
    # with sem:
    #     print sem.__dict__
    #     g = gevent.spawn(fuck)
    #     g.join()
    #     print "sleep ok exit!", ctime()
    _tree_path = NODE['TREE_PATH']

    meta = zk.get_node_dict(_tree_path)
    print meta['dirs']
    print zk.fix_tree_dirs()
