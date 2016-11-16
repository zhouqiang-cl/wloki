#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
from itertools import ifilter, groupby
import re
import string

from ipaddress import IPv4Network
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import undefer_group, load_only, joinedload
from torext import params
from torext.errors import ValidationError

from ..app import settings
from ..base.handlers import APIHandler
from ..node.models import NodeServers, TrackURL
from ..server.models import RawServer, ServerType, MAC, IPv4, VM, ServerStatus, VMHost
from ..errors import ParamsInvalidError
from ..utils import list_flat, merge_dict
from ..zookeeper import zk
from .privileges import AssetPrivilege


class AssetHandler(APIHandler):
    def get(self):
        raw = [merge_dict(self.json_decode(server.searchable_info),
                          {"status": server.validity})
               for server in RawServer.valid().with_entities(RawServer.searchable_info,
                                                             RawServer.validity)
               if server.searchable_info is not None]

        # compatible format for http://t.a.nosa.me/server/api/servers
        if self.get_argument('compatible', None):
            for el in raw:
                el['_id'] = el['sn']
                el['status'] = 'production' if el['status'] == ServerStatus.online\
                    else el['status']
                el['idc'] = el['idc'].rstrip(string.digits)
                if el.get('cpuModel') and isinstance(el['cpuModel'], list):
                    el['cpuModel'] = el['cpuModel'][0]
                if el.get('private_ip'):
                    el['private_ip'] = [i.split('/')[0] for i in el['private_ip']]
                if el.get('public_ip'):
                    el['public_ip'] = [i.split('/')[0] for i in el['public_ip']]

        self.write_json(raw)


class AssetQueryHandler(APIHandler):
    def get(self):
        fuzzy_word = self.get_argument("fuzzy_word", None)
        hostname = self.get_argument("hostname", None)
        if fuzzy_word:
            fuzzy_word = fuzzy_word.encode('utf8')
            return self.write_json(self.query_fuzzy(fuzzy_word))
        if hostname:
            hostname = hostname.encode('utf8')
            return self.write_json(self.query_hostname(hostname))

    def query_hostname(self, hostname):
        server = RawServer.query.with_entities(RawServer.searchable_info,
                                               RawServer.validity)\
            .filter_by(hostname=hostname).first_or_404()
        return merge_dict(self.json_decode(server.searchable_info),
                          {"status": server.validity})

    def query_fuzzy(self, fuzzy_word):
        return [merge_dict(self.json_decode(server.searchable_info),
                           {"status": server.validity})
                for server in RawServer.query.with_entities(RawServer.searchable_info,
                                                               RawServer.validity)
                    .filter(RawServer.searchable_info.like("%{}%".format(fuzzy_word)))]


class AssetServerStatusHandler(APIHandler):
    def get(self, sn):
        server = RawServer.query.load_only('validity').filter_by(sn=sn) \
            .first_or_404(msg="sn %s doesn't exists" % sn)
        return self.write_json({'status': server.validity})

    @params.simple_params(datatype='json')
    def post(self, sn):
        server = RawServer.query.load_only('validity').filter_by(sn=sn) \
            .first_or_404(msg="sn %s doesn't exists" % sn)
        try:
            status = getattr(ServerStatus, self.params['status'])
        except KeyError:
            raise ParamsInvalidError("parameter `status` missing")
        except AttributeError:
            raise ParamsInvalidError("parameter `status` invalid")
        else:
            if status == ServerStatus.creating and server.type == ServerType.vmh:
                if len(server.vms) != 0:
                    raise ParamsInvalidError("can't set vmh server with existed vm to creating")

        if status == ServerStatus.creating:
            server.reset()

        server.validity = status
        server.save()
        return self.write_json({"message": "server status update succeed"})


class AssetDetailHandler(APIHandler):
    def get(self, sn):
        server = VM.query.options(undefer_group('details'),
                                     joinedload(VM.vm_host)).filter_by(sn=sn)\
            .first_or_404(msg="sn %s doesn't exists" % sn)
        data = self.json_decode(server.searchable_info)\
            if server.searchable_info \
            else {"hostname": server.hostname, "sn": server.sn, "type": server.type}
        if server.type == ServerType.vm:
            if server.vm_host:
                data.update({"vm_host": {"hostname": server.vm_host.hostname,
                                         "sn": server.vm_host.sn},
                             "vm_name": server.vm_name})
        elif server.type == ServerType.vmh:
            data.update({"vms": [{"hostname": vm.hostname,
                                  "sn": vm.sn} for vm in server.vms]})
        data.update({"status": server.validity})

        # Node info
        ns = NodeServers.query.filter_by(server_id=server.id).all()
        data.update(
            on_nodes=[{'id': i.node_id,
                      'path': zk.without_expire.get_node_dir(i.node_id)}
                       for i in ns]
        )

        return self.write_json(data)

    def delete(self, sn):
        server = VMHost.query.options(joinedload(VMHost.nodes),
                                      joinedload(VMHost.vms))\
            .filter_by(sn=sn)\
            .first_or_404(msg="sn %s doesn't exists" % sn)

        if server.type == ServerType.vmh and len(server.vms) != 0:
            raise ParamsInvalidError("can't delete vmh server with vm bonded with")

        for node in server.nodes:
            node.remove()
        server.delete()
        return self.set_status(204)


class AssetQueryByTypeHandler(APIHandler):
    def get(self, _type):
        method_name = "query_%s" % _type
        getattr(self, method_name)()
        return

    def query_hostname(self):
        server_type = self.get_argument("type", None)
        if server_type:
            try:
                server_type = ServerType(server_type)
            except ValueError as e:
                raise ParamsInvalidError(str(e))
            query = RawServer.query.filter_by(type=ServerType(server_type))
        else:
            query = RawServer.query
            # raise ParamsInvalidError("invalid type %s" % server_type)

        idc = self.get_argument("idc", None)
        if idc:
            query = query.filter_by(idc=idc)

        return self.write_json([server.hostname for server in query])

    def query_idc(self):
        return self.write_json([server.idc for server in RawServer.query
                               .with_entities(RawServer.idc)
                               .distinct()
                               .filter(RawServer.idc.isnot(None))
                               .all()])


class ApplyParams(params.ParamSet):
    __datatype__ = "json"
    sn = params.RegexField(pattern="[a-zA-Z0-9-]+", required=True)
    hostname_prefix = params.RegexField(pattern="[a-zA-Z0-9-_]")
    hostname_pattern = params.RegexField(pattern="[a-zA-Z0-9*-_]")
    type = params.WordField(required=True)
    idc = params.WordField(required=True)
    network = params.Field()

    def validate_network(self, data):
        try:
            return IPv4Network(unicode(data))
        except Exception as e:
            raise ValidationError(str(e))

    def validate_type(self, data):
        try:
            return ServerType(data)
        except ValueError as e:
            raise ValidationError(str(e))

    def validate_hostname_pattern(self, value):
        if value.count("*") != 1:
            raise ValidationError('pattern must have 1 star(*) placeholder')
        return value


class AssetServerApplyHandler(APIHandler):
    @ApplyParams.validation_required
    def post(self):
        network, idc, sn, server_type = (self.params.network,
                                         self.params.idc,
                                         self.params.sn,
                                         self.params.type)
        ret = {"sn": sn, "idc": idc, "type": server_type}
        server_model = RawServer(sn=sn, type=server_type, idc=idc, validity=ServerStatus.creating)

        if self.params.hostname_prefix:
            prefix = self.params.hostname_prefix
            exists_hostnames = list_flat(RawServer.query.with_entities(RawServer.hostname)
                                         .filter(RawServer.hostname.like("{}%".format(prefix)))
                                         .filter_by(idc=idc)
                                         .with_for_update()
                                         .all())
            regex = "{}(?P<num>\d+)\.{}".format(prefix, idc)
            hostname_template = "{}{{num}}.{}".format(prefix, idc)
        elif self.params.hostname_pattern:
            pattern = self.params.hostname_pattern
            exists_hostnames = list_flat(RawServer.query.with_entities(RawServer.hostname)
                                         .filter(RawServer.hostname.like(pattern.replace("*", "%")))
                                         .with_for_update()
                                         .all())
            regex = re.escape(pattern).replace("\*", "(?P<num>\d+)")
            hostname_template = pattern.replace("*", "{num}")
        else:
            raise ValidationError("hostname_prefix or hostname_pattern must been provided")

        hostname = self._find_next_hostname(exists_hostnames, regex, hostname_template)

        ret["hostname"] = hostname
        server_model.hostname = hostname

        if network:
            all_servers = RawServer.query.options(load_only("private_ipv4s")).all()
            interfaces = ifilter(lambda x: x is not None,
                                 list_flat(s.private_ipv4s for s in all_servers))
            try:
                network, ifaces = ((k, g)
                                   for k, g in groupby(sorted(interfaces, key=lambda x: x.network),
                                                       key=lambda x: x.network)
                                   if k == network).next()
            except StopIteration:
                # !!! exclude first IP address in certain IP network for gateway equipment
                available_ips = list(network.hosts())[1:]
                selected_ip = available_ips.pop()
            else:
                # !!! exclude first IP address in certain IP network for gateway equipment
                available_ips = list(network.hosts())[1:]
                available_ips = set(available_ips) - set(i.ip for i in ifaces)
                selected_ip = available_ips.pop()

            server_model.private_ipv4s = [IPv4((unicode(selected_ip), network.prefixlen))]
            ret['private_ip'] = str(selected_ip)
            server_model.searchable_info = self.json_encode(
                merge_dict(ret, {"private_ip": server_model.private_ipv4s})
            )
        else:
            server_model.searchable_info = self.json_encode(ret)

        try:
            server_model.save()
        except IntegrityError as e:
            RawServer.rollback()
            raise ParamsInvalidError(str(e))
        self.write_json(ret)

    @classmethod
    def _find_next_hostname(cls, hostnames, regex, template):
        max = None
        for hostname in hostnames:
            matched = re.match(regex, hostname)
            if matched is not None:
                if max is None or int(matched.group("num")) > max:
                    max = int(matched.group("num"))

        if max is None:
            return template.format(num=0)
        else:
            return template.format(num=max + 1)



class AssetInfoUpdateHandler(APIHandler):
    @params.simple_params(datatype='json')
    def post(self):
        data = self.params
        sn, hostname, raw_type = data['sn'], data['hostname'], data['type']

        try:
            server_type = ServerType(raw_type)
        except ValueError:
            raise ParamsInvalidError("server type %s invalid" % raw_type)

        if not sn or not hostname:
            raise ParamsInvalidError("sn or hostname not allowed to be empty")

        server = RawServer.query.options(undefer_group('details')).filter_by(sn=sn).first()
        if server is None:
            server = RawServer(sn=sn,
                               hostname=hostname,
                               type=server_type,
                               validity=ServerStatus.online)
        else:
            server.hostname = hostname
            server.type = server_type
            # received assets update from vm after first boot up, make it online
            if server.validity == ServerStatus.creating:
                server.validity = ServerStatus.online

        server.idc = data['idc']
        server.MACs = filter(lambda x: not x.is_reserved, [MAC.from_string(s) for s in data.pop('mac', [])])
        data['macs'] = [str(mac) for mac in server.MACs]

        ip_set = [IPv4(s) for s in data.pop('ips', [])]
        server.private_ipv4s = filter(lambda x: x.ip.is_private and not x.ip.is_loopback, ip_set)
        server.public_ipv4s = filter(lambda x: not x.ip.is_private, ip_set)
        data['private_ip'] = [str(ip) for ip in server.private_ipv4s]
        data['public_ip'] = [str(ip) for ip in server.public_ipv4s]

        _check = lambda x: len(x) != 0 if isinstance(x, collections.Sized) else x is not None
        server.searchable_info = self.json_encode({k: v for k, v in data.iteritems() if _check(v)})

        vm_macs = data.pop('vms')
        if isinstance(vm_macs, collections.MutableSequence):
            vms = VM.polymorphic_query.with_entities(VM.id,
                                                     VM.MACs,
                                                     VM.vm_name,
                                                     VM.vm_host_id).all()
            for vm_name, macs in [(vm['vm_name'], vm['mac']) for vm in vm_macs]:
                macs_set = set(MAC.from_string(s) for s in macs)
                try:
                    vm = ifilter(lambda v: set(v.MACs) & macs_set, (v for v in vms if v.MACs)).next()
                except StopIteration:
                    continue
                if vm.vm_host_id != server.id or vm.vm_name != vm_name:
                    VM.query.filter_by(id=vm.id).update({VM.vm_name: vm_name, VM.vm_host_id: server.id})

        server.save()
        self.write_json({"message": "asset info update succeed"})


class AssetAgentConfigHandler(APIHandler):
    def get(self):
        import uwsgi
        md5 = self.get_argument('md5', None)
        if md5 and md5 == uwsgi.cache_get(settings.ASSET_HASH_KEY):
            self.set_status(304)
            return
        scripts_content = uwsgi.cache_get(settings.ASSET_SCRIPTS_CONTENT_KEY)
        self.write(scripts_content)


handlers = [
    ('', AssetHandler),
    ('/update', AssetInfoUpdateHandler),
    ('/query', AssetQueryHandler),
    ('/status/(.+)', AssetServerStatusHandler),
    ('/detail/(.+)', AssetDetailHandler),
    ('/query/(hostname|idc)', AssetQueryByTypeHandler),
    ('/apply', AssetServerApplyHandler),
    ('/agent_config', AssetAgentConfigHandler)
]
