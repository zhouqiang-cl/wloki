#!/usr/bin/env python
# -*- coding: utf-8 -*-
import binascii
import struct

from ipaddress import IPv4Interface
import msgpack
import enum
from sqlalchemy.orm import deferred, undefer_group, backref
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils.types.choice import ChoiceType

from loki.utils import encode_json
from loki.base.models import db, ModelMixin
from loki.utils.sqlalchemy_custom_type import BinaryObject


class MAC(object):
    TYPE_NUMBER = 50
    RESERVERD_ADDRESS = [
        '000000000000',
        'FFFFFFFFFFFF'
    ]

    def __init__(self, bin_str):
        self._mac = bin_str

    def for_json(self):
        return str(self)

    def __str__(self):
        return ":".join(binascii.hexlify(c) for c in self._mac)

    def __unicode__(self):
        return str(self)

    def __repr__(self):
        return "<MAC: %s>" % str(self)

    def __hash__(self):
        return hash(self._mac)

    def __eq__(self, other):
        if not isinstance(other, MAC):
            return str(self) == other
        else:
            return self._mac == other._mac

    @classmethod
    def from_string(cls, s):
        if isinstance(s, unicode):
            s = s.encode('utf8')
        return cls(binascii.unhexlify(str(s).replace(":", "")))

    @classmethod
    def bin_encode(cls, obj):
        return msgpack.ExtType(cls.TYPE_NUMBER, obj._mac)

    @classmethod
    def bin_decode(cls, code, bin_str):
        if code != cls.TYPE_NUMBER:
            return msgpack.ExtType(code, bin_str)
        return MAC(bin_str)

    @property
    def is_reserved(self):
        return binascii.hexlify(self._mac) in self.RESERVERD_ADDRESS


class IPv4(IPv4Interface):
    TYPE_NUMBER = 49

    def __init__(self, address):
        super(IPv4, self).__init__(address)

    def for_json(self):
        return str(self)

    @classmethod
    def bin_encode(cls, obj):
        return msgpack.ExtType(cls.TYPE_NUMBER, obj.ip.packed + chr(obj._prefixlen))

    @classmethod
    def bin_decode(cls, code, bin_str):
        if code != cls.TYPE_NUMBER:
            return msgpack.ExtType(code, bin_str)

        if len(bin_str) == 4:
            ip = bin_str
            prefix = 32
        elif len(bin_str) == 5:
            ip = bin_str[:-1]
            prefix = ord(bin_str[-1])
        else:
            raise ValueError("IPv4 value invalid %s" % bin_str)
        address = (struct.unpack("!L", ip)[0], prefix)
        return IPv4(address)


class ServerType(enum.Enum):
    raw = "raw"
    vm = "vm"
    vmh = "kvm"

    def for_json(self):
        return self.value


class ServerStatus(enum.Enum):
    online = 1
    maintenance = 2
    creating = 3

    def for_json(self):
        return self.name


class RawServer(db.Model, ModelMixin):
    __tablename__ = "servers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sn = db.Column(db.String(50), unique=True, nullable=False)
    hostname = db.Column(db.String(50), nullable=False)
    validity = db.Column(ChoiceType(ServerStatus, impl=db.Integer()),
                         nullable=False)
    type = db.Column(ChoiceType(ServerType, impl=db.String(20)))
    idc = deferred(db.Column(db.String(20)), group="details")
    ctime = deferred(db.Column(db.DateTime, default=db.func.now(), nullable=False), group="details")
    mtime = deferred(db.Column(db.DateTime, onupdate=db.func.now()), group="details")
    MACs = deferred(db.Column("macs",
                              BinaryObject(length=600,
                                           encoder=MAC.bin_encode,
                                           decoder=MAC.bin_decode),
                              default=[]),
                    group="details")
    private_ipv4s = deferred(db.Column(BinaryObject(length=400,
                                                    encoder=IPv4.bin_encode,
                                                    decoder=IPv4.bin_decode),
                                       default=[], unique=True),
                             group="details")
    public_ipv4s = deferred(db.Column(BinaryObject(length=400,
                                                   encoder=IPv4.bin_encode,
                                                   decoder=IPv4.bin_decode),
                                      default=[]),
                            group="details")
    searchable_info = deferred(db.Column("s_info", db.Text()), group="details")

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': ServerType.raw,
    }

    def reset(self):
        self.MACs = self.private_ipv4s = self.public_ipv4s = []
        self.vm_name = self.vm_host_id = None
        self.searchable_info = encode_json({"sn": self.sn,
                                            "hostname": self.hostname,
                                            "type": self.type,
                                            "idc": self.idc})

    @hybrid_property
    def is_valid(self):
        return self.validity.in_([ServerStatus.online, ServerStatus.maintenance])

    @classmethod
    def valid(cls):
        return cls.query.filter(cls.validity.in_([ServerStatus.online, ServerStatus.maintenance]))


class VM(RawServer):
    __mapper_args__ = {
        'polymorphic_identity': ServerType.vm,
        'polymorphic_on': RawServer.type,
    }
    __table_args__ = {
        'extend_existing': True,
    }

    vm_host_id = db.Column(db.Integer, db.ForeignKey("servers.id"), nullable=True)
    vm_name = db.Column(db.String(40), nullable=True)

    @hybrid_property
    def polymorphic_query(cls):
        return cls.query.filter_by(type=ServerType.vm).options(undefer_group('details'))


class VMHost(RawServer):
    __mapper_args__ = {
        'polymorphic_identity': ServerType.vmh,
        'polymorphic_on': RawServer.type,
    }
    __table_args__ = {
        'extend_existing': True
    }

    vms = db.relationship("VM", backref=backref('vm_host', remote_side=[VM.id]))

    @hybrid_property
    def polymorphic_query(cls):
        return cls.query.filter_by(type=ServerType.vmh).options(undefer_group('details'))


