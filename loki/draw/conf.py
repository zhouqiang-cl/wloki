# -*- coding: utf-8 -*-

# charts
#  \_ category
#      \_ type
#          \_ key

CHART_CONFIGS = [
    {
        'category': 'system',
        'name': u' 系统',
        'config': {},
        'items': [
            {
                'type': 'CPU',
                'items': [
                    {
                        'key': 'cpu.iowait',
                        'name': u'等待I/O操作CPU时间百分比',
                        'config': {}
                    },
                    {
                        'key': 'cpu.idle',
                        'name': u'空闲CPU时间百分比',
                        'config': {}
                    },
                    {
                        'key': 'cpu.system',
                        'name': u'系统使用CPU时间百分比',
                        'config': {}
                    },
                    {
                        'key': 'cpu.user',
                        'name': u'用户使用CPU时间百分比',
                        'config': {}
                    },
                ]
            },
            {
                'type': 'Memory',
                'items': [
                    {
                        'key': 'mem.memused',
                        'name': u'使用内存(KB)',
                        'config': {}
                    },
                    {
                        'key': 'mem.memtotal',
                        'name': u'内存容量(KB)',
                        'config': {}
                    },
                    {
                        'key': 'mem.memfree',
                        'name': u'空闲内存(KB)',
                        'config': {}
                    },
                    {
                        'key': 'mem.memused.percent',
                        'name': u'内存使用百分比',
                        'config': {}
                    },
                ]
            },
            {
                'type': 'Disk',
                'items': [
                    {
                        'key': 'disk.io.util',
                        'name': u'磁盘忙碌程度',
                        'config': {
                            'tags': ['device'],
                        },
                    },
                    {
                        'key': 'df.inodes.free',
                        'name': u'磁盘空闲inode',
                        'config': {
                            'tags': ['mount'],
                        }
                    },
                    {
                        'key': 'df.inodes.used.percent',
                        'name': u'磁盘使用inode百分比',
                        'config': {
                            'tags': ['mount'],
                        }
                    },
                    {
                        'key': 'disk.io.msec_total',
                        'name': u'每秒I/O次数',
                        'config': {
                            'tags': ['device'],
                        }
                    },
                    {
                        'key': 'df.inodes.used',
                        'name': u'磁盘使用inode',
                        'config': {
                            'tags': ['mount'],
                        }
                    },
                    {
                        'key': 'df.bytes.used',
                        'name': u'使用磁盘',
                        'config': {
                            'tags': ['mount'],
                        }
                    },
                    {
                        'key': 'df.bytes.used.percent',
                        'name': u'磁盘使用率',
                        'config': {
                            'tags': ['mount'],
                        }
                    },
                    {
                        'key': 'df.bytes.free',
                        'name': u'剩余磁盘',
                        'config': {
                            'tags': ['mount'],
                        }
                    }
                ]
            },
            {
                'type': 'NIC',
                'items': [
                    {
                        'key': 'net.if.in.dropped',
                        'name': u'每秒网卡接收丢包数',
                        'config': {}
                    },
                    {
                        'key': 'net.if.out.dropped',
                        'name': u'每秒网卡发送丢包数',
                        'config': {}
                    },
                    {
                        'key': 'net.if.out.bytes',
                        'name': u'发送速度(KB/秒)',
                        'config': {}
                    },
                    {
                        'key': 'net.if.in.bytes',
                        'name': u'接收速度(KB/秒)',
                        'config': {}
                    },
                ]
            },
            {
                'type': 'SWAP',
                'items': [
                    {
                        'key': 'mem.swaptotal',
                        'name': u'swap分区大小',
                        'config': {}
                    },
                    {
                        'key': 'mem.swapused',
                        'name': u'使用swap分区',
                        'config': {}
                    },
                    {
                        'key': 'mem.swapfree',
                        'name': u'空闲swap分区',
                        'config': {}
                    },
                    {
                        'key': 'mem.swapused.percent',
                        'name': u'swap分区使用百分比',
                        'config': {}
                    },
                ]
            },
            {
                'type': 'SYS',
                'items': [
                    {
                        'key': 'system.sys_uptime',
                        'name': u'系统运行时间',
                        'config': {}
                    },
                    {
                        'key': 'load.5min',
                        'name': u'过去5分钟系统平均负载',
                        'config': {}
                    },
                    {
                        'key': 'load.15min',
                        'name': u'过去15分钟系统平均负载',
                        'config': {}
                    },
                    {
                        'key': 'load.1min',
                        'name': u'过去1分钟系统平均负载',
                        'config': {}
                    },
                ]
            },
            {
                'type': 'NUM',
                'items': [
                    {
                        'key': 'kernel.files.allocated',
                        'name': u'打开句柄数',
                        'config': {}
                    },
                    {
                        'key': 'ss.estab',
                        'name': u'tcp数',
                        'config': {}
                    },
                    {
                        'key': 'system.num_sock',
                        'name': u'socket数',
                        'config': {}
                    },
                    {
                        'key': 'system.num_process',
                        'name': u'进程数',
                        'config': {}
                    },
                ]
            },
        ]
    }
]

HTTP_CONFIGS = [
    {
        'key': 'url.qps',
        'name': 'queries per second',
    },
    {
        'key': 'url.responsetime',
        'name': 'response time',
    },
    {
        'key': 'url.bandwidth',
        'name': 'bandwidth',
    },
    {
        'key': 'url.availability',
        'name': 'availability',
    },
]

DOMAIN_CONFIGS = [
    {
        'key': 'url.qps',
        'name': 'queries per second',
    },
    {
        'key': 'domain.responsetime',
        'name': 'response time',
    },
    {
        'key': 'url.bandwidth',
        'name': 'bandwidth',
    },
    {
        'key': 'domain.availability',
        'name': 'availability',
    },
]

USAGE_CONFIGS = [
    {
        'key': 'node.cpu_usage',
        'key_of_total': 'node.cpu_total',
        'key_of_total_unit': 'cores',
        'name': 'cpu usage(%)',
    },
    {
        'key': 'node.disk_usage',
        'key_of_total': 'node.disk_total',
        'key_of_total_unit': 'G',
        'name': 'disk usage(%)',
    },
    {
        'key': 'node.mem_usage',
        'key_of_total': 'node.mem_total',
        'key_of_total_unit': 'G',
        'name': 'memory usage(%)',
    },
    {
        'key': 'node.nic_rxkb_avg',
        'name': 'network rxkb',
        'default_info': '100MB',
    },
    {
        'key': 'node.nic_txkb_avg',
        'name': 'network txkb',
        'default_info': '100MB',
    },
]


AVAILABILITY_CONFIGS = [
    {
        'key': 'node.availability',
        'name': 'availability',
        'min': None,
    },
    {
        'key': 'node.responsetime',
        'name': 'response time',
    },
]
