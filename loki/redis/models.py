#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import socket

from sqlalchemy import and_, or_
from kazoo.client import KazooClient

from ..db import get_redis
from ..base.models import db, ModelMixin


class RedisInstance(db.Model, ModelMixin):
    """Redis instance information, no matter clustered nor standalone"""
    __tablename__ = "redis_instance"

    id = db.Column(db.BigInteger, primary_key=True)
    host = db.Column(db.String(64), nullable=False)
    port = db.Column(db.String(8), nullable=False)
    status = db.Column(db.String(8), nullable=True)
    master_host = db.Column(db.String(64), nullable=True)
    master_port = db.Column(db.String(8), nullable=True)
    cluster = db.Column(db.String(64), nullable=True)
    used_memory = db.Column(db.String(32), nullable=True)
    conf_maxmemory = db.Column(db.String(32), nullable=True)
    conf_dir = db.Column(db.String(64), nullable=True)
    conf_dbfilename = db.Column(db.String(64), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('host', 'port', name='uk_host_port'),
    )

    @classmethod
    def save_and_update(self, host, port, cluster=None, status='online', update=True):
        # If host is ip, gethostname
        if re.match(r'^\d+.\d+.\d+.\d+$', host):
            try:
                host = socket.gethostbyaddr(host)[0].replace('.nosa.me', '')
            except:
                print "!!DEBUG!! connect to redis exception"
        # If host end with '.nosa.me', delete that
        if re.match(r'^.+\.nosajia\.com$', host):
            host = host.replace('.nosa.me', '')

        try:
            # If need to update redis info
            if not update:
                raise ValueError('Just raise to get default value')
            r = get_redis(host=host+'.nosa.me', port=port, db=0)

            p_cmaxm = r.config_get(pattern='maxmemory')['maxmemory']
            p_cdir = r.config_get(pattern='dir')['dir']
            p_cfile = r.config_get(pattern='dbfilename')['dbfilename']
            p_usedm = r.info(section='memory')['used_memory']
            p_mhost = ''
            p_mport = ''
            
            repl_info = r.info(section='replication')
            if repl_info['role'] == 'slave':
                p_mhost = repl_info['master_host']
                p_mport = repl_info['master_port']
        except:
            p_cmaxm = ''
            p_cdir = ''
            p_cfile = ''
            p_usedm = ''
            p_mhost = ''
            p_mport = ''
        
        r_inst = RedisInstance.query.filter(and_(
                                                (RedisInstance.host == host),
                                                (RedisInstance.port == port)
                                            )\
                                    )\
                                    .with_for_update(read=True).first()
        if r_inst is not None:
            r_inst.status = status if status is not None else r_inst.status
            r_inst.master_port = p_mport
            r_inst.master_host = p_mhost
            if cluster is not None and len(cluster.strip()) > 0:
                if r_inst.cluster is None \
                or len(r_inst.cluster.strip(',').strip()) == 0:
                    r_inst.cluster = cluster
                elif r_inst.cluster.find(cluster) < 0:
                    r_inst.cluster = r_inst.cluster.strip(',').strip() + ',' + cluster
            r_inst.used_memory = p_usedm
            r_inst.conf_maxmemory = p_cmaxm
            r_inst.conf_dir = p_cdir
            r_inst.conf_dbfilename = p_cfile
        else:
            r_inst = RedisInstance(host = host,
                                    port = port,
                                    status = status if status is not None else r_inst.status,
                                    master_host = p_mhost,
                                    master_port = p_mport,
                                    cluster = cluster,
                                    used_memory = p_usedm,
                                    conf_maxmemory = p_cmaxm,
                                    conf_dir = p_cdir,
                                    conf_dbfilename = p_cfile)
        r_inst.save()


class CodisInstance(db.Model, ModelMixin):
    """Codis instance information"""
    __tablename__ = "codis_instance"
    __zkhost__ = {
        "STG":"pre-zk-ct0.db01:2181",
        "HLG":"sa-redis03-cnc0.hlg01:2181,sa-redis04-cnc0.hlg01:2181,sa-redis05-cnc0.hlg01:2181",
        "HY":"zk=app274.hy01:2181,app273.hy01:2181,app277.hy01:2181,app275.hy01:2181,app272.hy01:2181"
    }

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    zk = db.Column(db.String(8), nullable=False)
    zk_addr = db.Column(db.String(128), nullable=True)
    dashboard = db.Column(db.String(128), nullable=True)
    proxy = db.Column(db.String(256), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('name', 'zk', name='uk_name_zk'),
    )

    @classmethod
    def save_and_update(self, name, zk, update=True):
        name = str(name)
        zk = str(zk)
        if zk not in self.__zkhost__:
            raise ValueError('Unknown zk [%s]'%zk)
        zk_path_root = '/zk/codis/db_%s'%name

        try:
            kz = KazooClient(hosts=self.__zkhost__[zk], read_only=True, logger=None)
            kz.start()
            if not kz.exists(path=zk_path_root):
                raise ValueError('path [%s] don\'t exists on zk [%s]'%(zk_path_root, zk))
            
            # Get proxy info
            try:
                proxy = []
                for proxy_id in kz.get_children(zk_path_root+'/proxy'):
                    tmp_val = kz.get(zk_path_root+'/proxy/%s'%(proxy_id))[0]
                    tmp_val = json.loads(tmp_val)
                    proxy.append(tmp_val['id'] + ':' + tmp_val['addr'])
                proxy = ','.join(proxy)
            except Exception as e:
                proxy = ''
                print "!!DEBUG!! get proxy %s"%(str(e))
            # Get dashboard info
            try:
                dashboard = ''
                tmp_val = kz.get(zk_path_root+'/dashboard')[0]
                dashboard = json.loads(tmp_val)['addr'].split(':')
                # If hostname is ip, gethostname
                if re.match(r'^\d+.\d+.\d+.\d+$', dashboard[0]):
                    try:
                        dashboard[0] = socket.gethostbyaddr(dashboard[0])[0]
                    except:
                        pass
                # If hostname end with '.nosa.me', delete that
                if re.match(r'^.+\.nosajia\.com$', dashboard[0]):
                    dashboard[0] = dashboard[0].replace('.nosa.me', '')
                dashboard = 'http://' + ':'.join(dashboard)
            except Exception as e:
                dashboard = ''
                print "!!DEBUG!! get dashboard %s"%(str(e))
            # Get and save server info
            try:
                print "CCC 11"
                servs = []
                for group_id in kz.get_children(zk_path_root+'/servers'):
                    for serv in kz.get_children(zk_path_root+'/servers/%s'%group_id):
                        # Currently node name in %group_id is host:port, if not, we must dig into it :)
                        servs.append(serv)
                # Save redis info
                for r in servs:
                    tmp_val = r.split(':')
                    RedisInstance.save_and_update(host = str(tmp_val[0]),
                                                    port = int(tmp_val[1]),
                                                    status = 'online',
                                                    cluster = zk+'-'+name,
                                                    update = False)
            except Exception as e:
                print "!!DEBUG!! save redis %s"%(str(e))

            # Save codis info
            c_inst = CodisInstance.query.filter(and_(
                                                    (CodisInstance.name == name),
                                                    (CodisInstance.zk == zk)
                                                )\
                                            )\
                                            .with_for_update(read=True).first()
            if c_inst is not None:
                # If we fail to get dashboard & proxy info, do not replace
                c_inst.dashboard = c_inst.dashboard if dashboard == '' else dashboard
                c_inst.proxy = c_inst.proxy if proxy == '' else proxy
            else:
                c_inst = CodisInstance(name = name,
                                        zk = zk,
                                        dashboard = dashboard,
                                        proxy = proxy)
            c_inst.save()
        except:
            print "CCCC"
        finally:
            kz.stop()
            kz.close()
