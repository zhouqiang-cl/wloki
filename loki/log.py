# -*- coding: utf-8 -*-

import logging


# Initialize loggers

loki_log = logging.getLogger('loki')

app_log = logging.getLogger('loki.app')

tsdb_log = logging.getLogger('loki.tsdb')

zk_log = logging.getLogger('loki.zookeeper')
