#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ctypes import (
    Structure, Union, POINTER,
    pointer, get_errno, cast,
)
import ctypes.util
import ctypes


class struct_sysinfo(Structure):
    _fields_ = [
        ('uptime', ctypes.c_long),
        ('loads', ctypes.c_ulong * 3),
        ('totalram', ctypes.c_ulong),
        ('freeram', ctypes.c_ulong),
        ('sharedram', ctypes.c_ulong),
        ('bufferram', ctypes.c_ulong),
        ('totalswap', ctypes.c_ulong),
        ('freeswap', ctypes.c_ulong),
        ('procs', ctypes.c_ushort),
        ('pad', ctypes.c_ushort),
        ('totalhigh', ctypes.c_ulong),
        ('freehigh', ctypes.c_ulong),
        ('mem_unit', ctypes.c_uint),
        ('__padding__', ctypes.c_char * (20 - 2 * ctypes.sizeof(ctypes.c_long)
                                         - ctypes.sizeof(ctypes.c_int))),
    ]

libc = ctypes.CDLL(ctypes.util.find_library('c'))


def get_sysinfo():
    info = struct_sysinfo()
    ret = libc.sysinfo(pointer(info))
    if ret != 0:
        raise OSError(get_errno())
    return info


class SysInfo(object):
    def __init__(self, sysinfo):
        self.sysinfo = sysinfo

    @property
    def totalram(self):
        return self.sysinfo.mem_unit * self.sysinfo.totalram / (1024 ** 2)

    @property
    def totalswap(self):
        return self.sysinfo.mem_unit * self.sysinfo.totalswap / (1024 ** 2)

    @property
    def nprocs(self):
        return libc.get_nprocs()

    @property
    def nprocs_conf(self):
        return libc.get_nprocs_conf()


def export():
    sys_info = SysInfo(get_sysinfo())
    return {
        "data": {
            "mem": sys_info.totalram,
            "swap": sys_info.totalswap,
            "cpuCore": sys_info.nprocs_conf,
            "_cpuCore_online": sys_info.nprocs,
        },
    }

if __name__ == "__main__":
    from pprint import pprint
    pprint(export())
