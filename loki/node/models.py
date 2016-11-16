#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
from decimal import Decimal as D
import traceback
from types import NoneType

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import contains_eager

from ..base.models import db, ModelMixin
from ..errors import (FatalError,
                      DoesNotExist,
                      ValidationError)
from loki.zookeeper import zk
from ..server.models import RawServer


class NodeServers(db.Model, ModelMixin):
    __tablename__ = "node_servers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    node_id = db.Column(db.Integer, nullable=False)
    server_id = db.Column(db.Integer, db.ForeignKey("servers.id"), nullable=True)
    server = db.relationship(lambda: RawServer, backref='nodes')
    offline = db.Column(db.Boolean, nullable=False, index=True, default=False)
    traffic_ratio = db.Column(db.Numeric(precision=4, scale=3), nullable=True, default=None)

    __table_args__ = (
        db.UniqueConstraint('server_id', 'node_id', name='node_info_unique_index'),)

    @hybrid_property
    def validity(self):
        return self.server.validity

    @classmethod
    def change_traffic_ratio(cls, node_id, server_ids, ratio):
        minimum = D("0.001")
        try:
            assert isinstance(ratio, (D, NoneType)), "ratio should be a Decimal or None"
            nodes_ratio = [r[0] for r in cls.query.with_for_update(read=True)
                                            .with_entities(NodeServers.traffic_ratio)
                                            .filter((cls.node_id == node_id) &
                                                    ~(cls.server_id.in_(server_ids)))
                                            .all()]
            null_num = nodes_ratio.count(None)
            other_nodes_ratio_sum = sum(map(lambda x: minimum if x is None else x, nodes_ratio))
            if ratio is not None:
                if ratio * len(server_ids) + other_nodes_ratio_sum < D("1") \
                        and ratio * len(server_ids) + other_nodes_ratio_sum != D("0") \
                        and null_num == 0:
                    raise ValidationError("Not allow traffic ratio sum up 0 < x < 1")
                elif ratio * len(server_ids) + other_nodes_ratio_sum > D("1"):
                    raise ValidationError("Not allow traffic ratio sum up greater than 1")
            cls.query.filter(
                (cls.node_id == node_id) &
                (cls.server_id.in_(server_ids))
            ).update({'traffic_ratio': ratio}, synchronize_session=False)
            cls.commit()
        except ValidationError:
            raise
        except Exception as e:
            traceback.print_exc()
            raise FatalError(str(e))
        finally:
            db.session.rollback()

    @classmethod
    def add_servers(cls, node_id, hostnames):
        for hostname in hostnames:
            server = RawServer.query.filter_by(hostname=hostname).first()
            if not server:
                raise DoesNotExist("hostname %s not exists" % hostname)
            nodeserver = NodeServers(node_id=node_id, server_id=server.id)
            nodeserver.add()
        try:
            NodeServers.commit()
        except IntegrityError as e:
            raise ValidationError("some hostname already added to this node, error: %s" % str(e))
        except Exception as e:
            raise FatalError(str(e))
        return True

    @classmethod
    def remove_servers(cls, node_id, hostnames):
        try:
            subq = RawServer.query\
                            .with_entities(RawServer.id)\
                            .filter(RawServer.hostname.in_(hostnames))\
                            .subquery()
            n = NodeServers.query.filter(
                (NodeServers.node_id == node_id) &
                (NodeServers.server_id.in_(subq))
            ).delete(synchronize_session="fetch")
            NodeServers.commit()
        except Exception as e:
            raise FatalError(str(e))
        return n

    @classmethod
    def _make_get_by_node_query(cls, exclude_offline=False):
        query = cls.query.join(NodeServers.server)\
                         .options(contains_eager(NodeServers.server)) \
                         .filter(RawServer.is_valid == True)
        if exclude_offline:
            # only obtain online NodeServer if exclude_offline is True
            query = query.filter(NodeServers.traffic_ratio != 0)
        return query

    @classmethod
    def get_by_node_id(cls, node_id, exclude_offline=False):
        """
        :type node_id: int
        :type exclude_offline: bool
        :rtype: collections.Sequence[NodeServers]
        """
        query = cls._make_get_by_node_query(exclude_offline)
        query = query.filter(cls.node_id == node_id)
        return query.all()

    @classmethod
    def get_by_node_ids(cls, node_ids, exclude_offline=False):
        """
        :type node_ids: collections.Iterable[int]
        :type exclude_offline: bool
        :rtype: collections.Sequence[NodeServers]
        """
        query = cls._make_get_by_node_query(exclude_offline)
        query = query.filter(cls.node_id.in_(node_ids))
        return query.all()

    @classmethod
    def get_by_node(cls, node_id, recursive=True, exclude_offline=False):
        node_ids = []
        if recursive:
            node_ids = zk.without_expire.get_node_children(node_id, recursive)
        node_ids.append(node_id)
        return cls.get_by_node_ids(node_ids, exclude_offline)


class NodeUpstream(db.Model, ModelMixin):
    __tablename__ = "node_upstream"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    node_id = db.Column(db.Integer, nullable=False, index=True, unique=True)
    name = db.Column(db.String(50), nullable=False, index=True, unique=True)
    port = db.Column(db.Integer, nullable=True)
    ip_hash = db.Column(db.Integer, nullable=True)

    @classmethod
    def update(cls, node_id, data):
        try:
            cls.query.filter(
                (cls.node_id == node_id)
            ).update(data, synchronize_session=False)
            cls.commit()
        except ValidationError:
            raise
        except Exception as e:
            traceback.print_exc()
            raise FatalError(str(e))
        finally:
            db.session.rollback()


class NodeDocker(db.Model, ModelMixin):
    __tablename__ = "node_docker"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    node_id = db.Column(db.Integer, nullable=False, index=True, unique=True)
    isDocker = db.Column(db.Integer, nullable=True)
    publishedPort = db.Column(db.Integer, nullable=True)

    @classmethod
    def update(cls, node_id, data):
        try:
            cls.query.filter(
                (cls.node_id == node_id)
            ).update(data, synchronize_session=False)
            cls.commit()
        except ValidationError:
            raise
        except Exception as e:
            traceback.print_exc()
            raise FatalError(str(e))
        finally:
            db.session.rollback()


class TrackURL(db.Model, ModelMixin):
    __tablename__ = "trackurl"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    service_id = db.Column(db.Integer, nullable=True, index=True)
    product_id = db.Column(db.Integer, nullable=False, index=True)
    domain = db.Column(db.String(50), nullable=False)
    path = db.Column(db.String(50), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('domain', 'path', name='trackurl_unique_index'),)
