# -*- coding: utf-8 -*-

import re
from collections import defaultdict
from sqlalchemy.exc import IntegrityError
from decimal import Decimal as D  # NOQA
from torext import params

from .. import errors
from ..base.handlers import APIHandler
from ..zookeeper import zk, NodeNotExistError
from ..zookeeper import ValueConflictError, ArgumentError, NodeValueError, NoNodeError
from ..server.models import RawServer
from ..contacter import set_contacter_of_node, get_contacter_of_node
from .models import NodeServers, TrackURL, NodeUpstream, NodeDocker
from .nodes import TreeNode, NodeType, _Context
from ..privilege import require_node_privileges
from .privileges import NodePrivilege


def format_nodes(raw):
    bottom_ids = [i['id'] for i in raw]
    for i in raw:
        i['id'] = i['id']
        i['parent'] = i.pop('pId')
        try:
            bottom_ids.remove(i['parent'])
        except ValueError:
            pass
        if i['parent'] == 0:
            i['parent'] = '#'
            i['type'] = 'root'
        i['text'] = i.pop('name')

    for i in raw:
        if i['id'] in bottom_ids:
            i['type'] = 'bottom'


class NodesHandler(APIHandler):
    @params.define_params({
        'with_path': params.IntegerField(choices=(0, 1), default=0)
    })
    def get(self):
        #nodes = zk.without_expire.get_tree_meta()
        #format_nodes(nodes)
        #self.write_data(nodes)

        root_node = TreeNode(1)

        if self.params.with_path:
            data = [
                {
                    'text': i.name,
                    'id': i.id,
                    'parent': '#' if i.parent is 0 else i.parent,
                    'path': i.path,
                    'type': 'bottom' if i.type is NodeType.leaf else 'node',
                } for i in root_node.dfs_generator()]
        else:
            data = [
                {
                    'text': i.name,
                    'id': i.id,
                    'parent': '#' if i.parent is 0 else i.parent,
                    'type': 'bottom' if i.type is NodeType.leaf else 'node',
                } for i in root_node.dfs_generator()]
        self.write_data(data)

    @require_node_privileges(NodePrivilege.create_node, lambda c: int(c.handler.get_argument('parent_id')))
    def post(self):
        parent_id = int(self.get_argument('parent_id'))
        name = self.get_argument('name')
        if not re.match(u'^[\u4e00-\u9fa5\w-]+$', name):
            raise errors.ParamsInvalidError('name could only contains character')
        node_id = zk.get_next_id()
        try:
            zk.add_tree_node(dict(
                id=node_id,
                pId=parent_id,
                name=name,
            ))
        except ValueConflictError:
            raise errors.ParamsInvalidError('node name %s conflict' % name)
        self.write_data({
            'id': node_id,
            'name': name
        })


class NodesQueryHandler(APIHandler):
    def get(self):
        node_id = self.get_argument('node_id', None)
        path = self.get_argument('path', None)
        with_height = self.get_argument('with_height', False)
        try:
            if node_id is not None:
                node = TreeNode(int(node_id), with_path=True)
            elif path is not None:
                node_dirs = zk.without_expire.get_dirs_meta()
                if path in node_dirs:
                    node = TreeNode(node_dirs[path], with_path=True)
                else:
                    raise NoNodeError(u"node path %s not existed" % path)
            else:
                raise errors.ValidationError("node_id or path argument is required")
            data = {
                'id': node.id,
                'pId': node.parent,
                'dir': node.path,
                'name': node.name,
                'level': node.level,
            }

            if with_height:
                data['height'] = node.height

        except (NodeValueError, NoNodeError, NodeNotExistError) as e:
            raise errors.DoesNotExist(unicode(e))
        except (TypeError, ValueError) as e:
            raise errors.ValidationError(e)
        self.write_data(data)


class UserNodesHandler(APIHandler):
    @params.define_params({
        'with_path': params.IntegerField(choices=(0, 1), default=0)
    })
    def get(self):
        # root_node = TreeNode(1)

        node_ids = self.user.get_accessible_nodes()

        if node_ids is None:
            self.write_data([])
            return

        if self.params.with_path:
            def format_node(i):
                return {
                    'text': i.name,
                    'id': i.id,
                    'parent': '#' if i.parent is 0 else i.parent,
                    'path': i.path,
                    'type': 'bottom' if i.type is NodeType.leaf else 'node',
                }
        else:
            def format_node(i):
                return {
                    'text': i.name,
                    'id': i.id,
                    'parent': '#' if i.parent is 0 else i.parent,
                    'type': 'bottom' if i.type is NodeType.leaf else 'node',
                }

        node_context = _Context()
        data_dict = {}

        for i in node_ids:
            tn = TreeNode(i, _context=node_context)
            # Get child nodes
            for n in tn.dfs_generator():
                if n.id not in data_dict:
                    data_dict[n.id] = format_node(n)
            # Get parent nodes
            for n in tn.parents:
                if n.id not in data_dict:
                    data_dict[n.id] = format_node(n)

        self.write_data(data_dict.values())
        # self.write_data(data)


class NodesItemHandler(APIHandler):
    def get(self, node_id):
        node_id = int(node_id)
        try:
            node = TreeNode(node_id, with_path=True)
            data = {
                'id': node.id,
                'pId': node.parent,
                'dir': node.path,
                'name': node.name,
            }
        except (NodeValueError, NodeNotExistError, NoNodeError):
            raise errors.DoesNotExist("node id %s not exist" % node_id)
        contacter = get_contacter_of_node(node_id)
        if contacter:
            data['contacter'] = contacter
        self.write_data(data)

    @require_node_privileges(NodePrivilege.manage_node, lambda c: int(c.args[0]))
    def post(self, node_id):
        node_id = int(node_id)
        pid = self.get_argument('pId', None)
        name = self.get_argument('name', None)

        if pid:
            node = {
                'id': node_id,
                'pId': int(pid),
                'name': zk.get_node_name(node_id)
            }
        elif name:
            node = {
                'id': node_id,
                'pId': zk.get_node_pid(node_id),
                'name': name
            }
        else:
            raise errors.ParamsInvalidError(
                'One of pId or name must be passed')

        try:
            zk.move_tree_node(node)
        except (ValueConflictError, ArgumentError), e:
            raise errors.ParamsInvalidError(str(e))

        self.write_data(node)

    @require_node_privileges(NodePrivilege.manage_node, lambda c: int(c.args[0]))
    def delete(self, node_id):
        node_id = int(node_id)
        if [x for x in zk.get_node_children(node_id) if x != node_id]:
            raise errors.OperationNotAllowed(u'不允许删除拥有后代的节点')
        servers_num = NodeServers.query.filter_by(node_id=node_id).count()
        if servers_num:
            raise errors.OperationNotAllowed(
                u'不允许删除关联有服务器的节点，服务器数: %s' % servers_num)
        zk.del_tree_node(node_id)
        self.set_status(204)
        return


class NodeDomainsAllHandler(APIHandler):

    def get(self):
        def reducer(x, y):
            # service_id = y.pop('service_id')
            key = y.pop('product_id')
            x[key].append(y)
            return x

        if self.get_argument('for_draw', False):
            # TODO: remove this dirty workaround, exclude URL bound with node `SRE` to
            # accelerate FE TSDB query
            select_oj = TrackURL.query.filter(TrackURL.product_id != 13)
        else:
            select_oj = TrackURL.query.all()
        args = ["product_id", "domain", "path"]
        ret = reduce(reducer,
                     (o.to_dict(*args) for o in select_oj),
                     defaultdict(list))

        self.write_data(ret)


class NodeDomainsHandler(APIHandler):

    args = ["id", "domain", "path"]

    def get(self, node_id):
        select_oj = TrackURL.query.filter_by(product_id=int(node_id)).all()
        ret = [o.to_dict(*self.args) for o in select_oj]

        self.write_data(ret)

    @require_node_privileges(NodePrivilege.manage_node_relatives, lambda c: int(c.args[0]))
    @params.simple_params(datatype="json")
    def post(self, node_id):
        domain, path = (
            self.params["domain"].strip(),
            self.params["path"].strip(),
        )
        record = TrackURL(
            domain=domain,
            path=path,
            product_id=node_id
        )
        try:
            ret = record.save()
            if ret:
                self.write_json({
                    "id": record.id,
                    "domain": record.domain,
                    "path": record.path,
                    "product_id": record.product_id
                })
            else:
                self.api_error(400, "create fail")
        except IntegrityError:
            self.api_error(400, "duplicated record")


class NodeDomainsItemHandler(APIHandler):
    args = ["id", "domain", "path"]

    def get(self, node_id, domain_id):
        domain = TrackURL.query.filter(
            (TrackURL.id == domain_id) &
            (TrackURL.product_id == node_id)).first()
        if not domain:
            raise errors.DoesNotExist('domain id %s not found' % domain_id)
        else:
            data = domain.to_dict(*self.args)
            self.write_json(data)

    @require_node_privileges(NodePrivilege.manage_node_relatives, lambda c: int(c.args[0]))
    def delete(self, node_id, domain_id):
        domain = TrackURL.query.filter(
            (TrackURL.id == domain_id) &
            (TrackURL.product_id == node_id)).first()
        if not domain:
            raise errors.DoesNotExist('domain id %s not found' % domain_id)
        else:
            domain.delete()
            self.set_status(204)
        return


class NodeServersHandler(APIHandler):
    class NodeServersPostParams(params.ParamSet):
        __datatype__ = 'json'
        server_ids = params.ListField('server_ids invalid',
                                      item_field=params.IntegerField(),
                                      required=True)
        traffic_ratio = params.Field("ratio invalid", required=True)

        def validate_traffic_ratio(self, value):
            try:
                if value is None:
                    return None
                ratio = str(value)
                v = D(ratio)
            except Exception as e:
                raise errors.ValidationError(str(e))
            return v

    @require_node_privileges(NodePrivilege.manage_node_relatives, lambda c: int(c.args[0]))
    @params.simple_params(datatype="json")
    def delete(self, node_id):
        # todo: add zk sync
        hostnames = self.params['hostnames']
        if NodeServers.remove_servers(node_id, hostnames):
            self.write_json(dict(
                status=True,
                message="deleted %s from %s succeed" % (hostnames, node_id),
            ))
        else:
            self.set_status(404)
            return

    @require_node_privileges(NodePrivilege.manage_node_relatives, lambda c: int(c.args[0]))
    @params.simple_params(datatype="json")
    def put(self, node_id):
        # todo: add zk sync
        hostnames = self.params['hostnames']
        if NodeServers.add_servers(node_id, hostnames):
            self.write_json(dict(
                status=True,
                message="create %s from %s succeed" % (hostnames, node_id),
            ))
        else:
            self.write_json(dict(
                status=True,
                message="create %s from %s fail" % (hostnames, node_id),
            ), code=400)
            return

    @require_node_privileges(NodePrivilege.manage_node_relatives, lambda c: int(c.args[0]))
    @NodeServersPostParams.validation_required
    def post(self, node_id):
        server_ids = self.params.server_ids
        ratio = self.params.traffic_ratio
        NodeServers.change_traffic_ratio(node_id, server_ids, ratio)
        self.write_json({
            "status": True,
            "message": "change traffic ratio for servers succeed"
        })


class ServerSearchHandler(APIHandler):
    def get(self):
        hostname = self.get_argument('hostname')

        server = RawServer.query.filter_by(hostname=hostname).first()
        if not server:
            raise errors.DoesNotExist('server %s not found' % hostname)

        ns = NodeServers.query.filter_by(server_id=server.id).all()

        data = {
            'hostname': server.hostname,
            'sn': server.sn,
            'dirs': [{'node_id': i.node_id,
                      'dir': zk.without_expire.get_node_dir(i.node_id)} for i in ns]
        }

        self.write_data(data)


class ContacterHandler(APIHandler):
    def get(self):
        node_id = self.get_argument('node_id')
        self.write_data(get_contacter_of_node(node_id))
        self.finish()

    def post(self):
        node_id = self.get_argument('node_id')
        contacter = str(self.get_argument('contacter'))
        contacter = ','.join(map(str.strip, contacter.split(',')))
        set_contacter_of_node(node_id, contacter)
        self.set_status(200)
        self.finish()


class NodeUpstreamAllHandler(APIHandler):

    def get(self):
        data = []

        select_oj = NodeUpstream.query.all()
        args = ["id", "node_id", "name", "port", "ip_hash"]
        upstream = [o.to_dict(*args) for o in select_oj]

        args = ["isDocker", "publishedPort"]
        for i in upstream:
            node_id = i["node_id"]
            select_oj = NodeDocker.query.filter_by(node_id=int(node_id)).all()
            if len(select_oj) == 1:
                docker = select_oj[0].to_dict(*args)
            else:
                docker = {}
                for j in args:
                    docker[j] = "无"
            i.update(docker)
            data.append(i)

        self.write_data(data)


class NodeUpstreamHandler(APIHandler):

    def get(self, node_id):
        select_oj = NodeUpstream.query.filter_by(node_id=int(node_id)).all()
        args = ["id", "node_id", "name", "port", "ip_hash"]
        if len(select_oj) == 1:
            upstream = select_oj[0].to_dict(*args)
        else:
            upstream = {}
            for i in args:
                upstream[i] = "无"

        select_oj = NodeDocker.query.filter_by(node_id=int(node_id)).all()
        args = ["isDocker", "publishedPort"]
        if len(select_oj) == 1:
            docker = select_oj[0].to_dict(*args)
        else:
            docker = {}
            for i in args:
                docker[i] = "无"

        upstream.update(docker)
        self.write_data(upstream)

    @require_node_privileges(NodePrivilege.manage_node_relatives, lambda c: int(c.args[0]))
    @params.simple_params(datatype="json")
    def post(self, node_id):
        node_id = int(node_id)

        select_oj = NodeUpstream.query.filter_by(node_id=node_id).all()
        if len(select_oj) == 0:
            data = {
                "node_id": node_id,
                "name": self.params["name"].strip(),
                "port": 8080,
                "ip_hash": 0
            }

            record = NodeUpstream(**data)
            try:
                ret = record.save()
                if ret:
                    self.write_json({
                        "id": record.id,
                        "node_id": record.node_id,
                        "name": record.name,
                        "port": record.port,
                        "ip_hash": record.ip_hash
                    })
                else:
                    self.api_error(400, "create fail")
            except IntegrityError:
                self.api_error(400, "duplicated record")
            return

        args = ["name", "port", "ip_hash"]
        data = select_oj[0].to_dict(*args)
        for i in args:
            if i in self.params:
                if i == "name":
                    data["name"] = self.params["name"].strip()
                else:
                    data[i] = self.params[i]

        NodeUpstream.update(node_id, data)
        return self.get(node_id)

    @require_node_privileges(NodePrivilege.manage_node_relatives, lambda c: int(c.args[0]))
    def delete(self, node_id):
        node_id = int(node_id)

        deleted = False

        select_oj = NodeUpstream.query.filter_by(node_id=node_id).first()
        if select_oj:
            select_oj.delete()
            deleted = True

        select_oj = NodeDocker.query.filter_by(node_id=node_id).first()
        if select_oj:
            select_oj.delete()
            deleted = True

        if not deleted:
            raise errors.DoesNotExist('upstream %s not found' % node_id)
        else:
            self.set_status(204)


class NodeDockerAllHandler(APIHandler):

    def get(self):
        select_oj = NodeDocker.query.all()
        args = ["id", "node_id", "isDocker", "publishedPort"]
        ret = [o.to_dict(*args) for o in select_oj]

        self.write_data(ret)


class NodeDockerHandler(APIHandler):

    def get(self, node_id):
        select_oj = NodeDocker.query.filter_by(node_id=int(node_id)).all()
        args = ["id", "node_id", "isDocker", "publishedPort"]
        if len(select_oj) == 1:
            ret = select_oj[0].to_dict(*args)
        else:
            ret = {}
            for i in args:
                ret[i] = "无"

        self.write_data(ret)

    @require_node_privileges(NodePrivilege.manage_node_relatives, lambda c: int(c.args[0]))
    @params.simple_params(datatype="json")
    def post(self, node_id):
        node_id = int(node_id)

        select_oj = NodeDocker.query.filter_by(node_id=node_id).all()
        if len(select_oj) == 0:
            data = {"node_id": node_id}

            for i in ["isDocker", "publishedPort"]:
                if i in self.params:
                    data[i] = self.params[i]
                else:
                    data[i] = 0

            record = NodeDocker(**data)
            try:
                ret = record.save()
                if ret:
                    self.write_json({
                        "id": record.id,
                        "node_id": record.node_id,
                        "isDocker": record.isDocker,
                        "publishedPort": record.publishedPort
                    })
                else:
                    self.api_error(400, "create fail")
            except IntegrityError:
                self.api_error(400, "duplicated record")
            return

        args = ["id", "node_id", "isDocker", "publishedPort"]
        data = select_oj[0].to_dict(*args)
        for i in args:
            if i in self.params:
                data[i] = self.params[i]

        NodeDocker.update(node_id, data)
        return self.get(node_id)

    @require_node_privileges(NodePrivilege.manage_node_relatives, lambda c: int(c.args[0]))
    def delete(self, node_id):
        node_id = int(node_id)

        select_oj = NodeDocker.query.filter_by(node_id=node_id).first()
        if not select_oj:
            raise errors.DoesNotExist('docker %s not found' % node_id)
        else:
            select_oj.delete()
            self.set_status(204)


handlers = [
    ('', NodesHandler),
    ('/query', NodesQueryHandler),  # new node query api
    ('/(\d+)', NodesItemHandler),  # for legacy usage
    ('/user_nodes', UserNodesHandler),
    ('/domains', NodeDomainsAllHandler),
    ('/(\d+)/domains', NodeDomainsHandler),
    ('/(\d+)/domains/(\d+)', NodeDomainsItemHandler),
    ('/(\d+)/servers', NodeServersHandler),
    ('/upstream', NodeUpstreamAllHandler),
    ('/(\d+)/upstream', NodeUpstreamHandler),
    ('/docker', NodeDockerAllHandler),
    ('/(\d+)/docker', NodeDockerHandler),

    # TODO move to other modules
    ('/server_search', ServerSearchHandler),
    ('/contacter', ContacterHandler),
]
