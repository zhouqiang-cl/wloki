# -*- coding: utf-8 -*-

from torext import params
import json
import socket
from ..base.handlers import BaseHandler, APIHandler
from .models import DataNode, DataSource, DataBase, Server, MySQLInstances

class IndexHandler(BaseHandler):
    """This class will manage Cobar Cluster Information"""

    def get(self):
        self.render('ocean/index.html')

class ReplSpiderHandler(BaseHandler):
    """This class will manage Cobar Cluster Information"""

    def get(self):
        self.render('ocean/repl_spider.html')

class CobarTree(APIHandler):
    """CobarTree class will manage Cobar Cluster Information"""

    def get(self):

        args = ["cluster","cobar_ip","cobar_adm_port"]
        select_obj = Server.query.all()
        ret = [data.to_dict(*args) for data in select_obj]
        self.write_data(ret)

class CobarInfo(APIHandler):
    """CobarInfo class will manage Cobar Cluster Information"""

    def get(self):

        args = ["cobar_ip","cluster","cobar_adm_port","uptime","used_memory",
                "total_memory","max_memory","reload_time","rollback_time",
                "charset","status"
        ]
        select_obj = Server.query.all()

        ret = [data.to_dict(*args) for data in select_obj]
        
        self.write_data(ret)

class DataNodeList(APIHandler):
    """DataNodeList class will manage clustered datanode"""

    @params.simple_params(datatype="json")
    def post(self):
        cluster, cobar_ip, cobar_adm_port=(
            self.params["cluster"],
            self.params["cobar_ip"],
            self.params["cobar_adm_port"]
        )

        args = ["name","datasource","index","cobar_ip","cobar_user_port",
                "cobar_adm_port","cluster"
        ]

        select_obj = DataNode.query.filter((DataNode.cobar_ip==cobar_ip) &
            (DataNode.cluster==cluster) & (DataNode.cobar_adm_port==cobar_adm_port)
            ).all()

        ret = [o.to_dict(*args) for o in select_obj]
        self.write_data(ret)

class DataSourceList(APIHandler):
    """DataSourceList class will manage clustered datanode"""

    @params.simple_params(datatype="json")
    def post(self):
        name, cobar_ip, cobar_adm_port=(
            self.params["name"],
            self.params["cobar_ip"],
            self.params["cobar_adm_port"]
        )

        args = ["name","host","port","schema","cobar_ip","cobar_user_port",
                "cobar_adm_port","cluster"
        ]

        select_obj = DataSource.query.filter((DataSource.cobar_ip==cobar_ip) &
            (DataSource.name==name) & (DataSource.cobar_adm_port==cobar_adm_port)
            ).all()

        ret = [o.to_dict(*args) for o in select_obj]
        self.write_data(ret)

class MySQLReplication(APIHandler):
    """MySQLReplication class will manage clustered datanode"""

    @params.simple_params()
    def get(self):
        database =(
            self.params["database"]
        )

        args = ["host", "ip", "port", "masterhost", "masterip", "masterport"]

        select_obj = MySQLInstances.query.filter(MySQLInstances.dbs.like('%"'+database+'"%')).all()

        nodes = []
        links = []
        ms    = []
        for i in select_obj:
            if i.masterhost != "":
                links.append({"from": i.masterhost + ":" + str(i.masterport), "to":i.host + ":" + str(i.port)})

            if i.masterhost+":"+str(i.masterport) in ms:
                pass
            else:
                ms.append(i.masterhost+":"+str(i.masterport))

        for i in select_obj:
            if i.host+":"+str(i.port) in ms or i.masterhost == "":
                nodes.append({"key":i.host + ":" + str(i.port), "color":"orange"})
            else:
                nodes.append({"key":i.host + ":" + str(i.port), "color":"lightblue"})

        for m in ms:
            if {"key":m, "color":"orange"} not in nodes and m!=":0":
                nodes.append({"key":m, "color":"orange"} )


        #ret = [o.to_dict(*args) for o in select_obj]
        self.write_data({"nodes":nodes, "links":links})

    
handlers = [
    ('', IndexHandler),
    ('/repl_spider', ReplSpiderHandler),
    ('/api/cobar', CobarInfo),
    ('/api/cobartree', CobarTree),
    ('/api/datanode', DataNodeList),
    ('/api/datasource', DataSourceList),
    ('/api/spider', MySQLReplication),
]

if __name__ == "main":
    CobarInfo.get()
