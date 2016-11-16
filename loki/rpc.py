#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from gevent import sleep
from kazoo.protocol.states import EventType
from pbrpc.rpc_channel import RpcChannel, Callback
from pbrpc.rpc_controller import RpcController
from pbrpc.utils import RpcException

from zookeeper import zk
from gangr_rpc_pb2 import GangrService_Stub
from gangr_rpc_pb2 import EchoRequest
from gangr_rpc_pb2 import JobRpcRequest

log = logging.getLogger("GangrRpc")

__services__ = {}


def get_rpc_service(path):
    if path not in __services__:
        __services__[path] = init_rpc_service(path)
    return __services__[path]


def init_rpc_service(path):
    def watcher(event):
        zk.without_expire.exists(path, watcher)
        if event.type in (EventType.CREATED, EventType.CHANGED):
            value, _ = zk.without_expire.get(path)
            addr, port = value.split(":")
            _service = RpcService(str(addr), int(port))
            __services__[path] = _service
        if event.type is EventType.DELETED:
            __services__.pop(path, None)

    if zk.without_expire.exists(path, watcher):
        value, _ = zk.without_expire.get(path)
        addr, port = value.split(":")
        service = RpcService(str(addr), int(port))
        return service
    else:
        raise RpcException("rpc service unavailable now")


class RpcService(object):
    def __init__(self, address, port):
        channel = RpcChannel(address, port)
        self.controller = RpcController()
        self.service = GangrService_Stub(channel)

    def echo(self, data):
        callback = Callback()
        request = EchoRequest()
        request.str = str(data)
        self.service.echo(self.controller, request, callback)
        if callback.response:
            return callback.response.str
        elif callback.error_message:
            raise RpcException(callback.error_message)

    def pause_job(self, job_id):
        callback = Callback()
        request = JobRpcRequest()
        request.job_id = long(job_id)
        self.service.pause_job(self.controller, request, callback)
        if callback.response:
            return callback.response.status
        elif callback.error_message:
            raise RpcException(callback.error_message)

    def continue_job(self, job_id):
        callback = Callback()
        request = JobRpcRequest()
        request.job_id = long(job_id)
        self.service.continue_job(self.controller, request, callback)
        if callback.response:
            return callback.response.status
        elif callback.error_message:
            raise RpcException(callback.error_message)

    def stop_job(self, job_id):
        callback = Callback()
        request = JobRpcRequest()
        request.job_id = long(job_id)
        self.service.stop_job(self.controller, request, callback)
        if callback.response:
            return callback.response.status
        elif callback.error_message:
            raise RpcException(callback.error_message)


if __name__ == "__main__":
    from settings import ZK_GANGR_PATH
    init_rpc_service(ZK_GANGR_PATH)
    while True:
        try:
            service = get_rpc_service(ZK_GANGR_PATH)
            print service.continue_job(1111)
        except Exception, e:
            print e
        sleep(5)
