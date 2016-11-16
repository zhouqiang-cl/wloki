# -*- coding: utf-8 -*-

import json
from collections import defaultdict
from .db import get_redis
from .settings import WHO_PERSON_LIST_ADDR
from .utils import asyncrequest
CONTACTER_PREFIX = 'contacter'
CONTACTERS_ID = CONTACTER_PREFIX+':ids'

def gen_contacter_key(person_id):
    return '%s:%s' % (CONTACTER_PREFIX, person_id)

def gen_node_key(node_id):
    return '%s:node:%s' % (CONTACTER_PREFIX, node_id)

def get_all_ids():
    rds = get_redis()
    return rds.smembers(CONTACTERS_ID)

def set_contacter(person_id, **kwargs):
    rds = get_redis()
    for k, v in kwargs.iteritems():
        rds.hset(gen_contacter_key(person_id), k, v)

def get_contacter(person_id):
    rds = get_redis()
    return rds.hgetall(gen_contacter_key(person_id))

def set_contacter_of_node(node_id, contacter): # contacters is a list()
    rds = get_redis()
    key = gen_node_key(node_id)
    rds.set(key, contacter)

def get_contacter_of_node(node_id):
    rds = get_redis()
    key = gen_node_key(node_id)
    return rds.get(key)

def sync_contacters():
    rds = get_redis()
    focused_keys = ['id', 'phone', 'mail']
    persons = json.loads(asyncrequest('GET', WHO_PERSON_LIST_ADDR).content)
    for p in persons:
        person_id = p.get('id')
        if not rds.sismember(CONTACTERS_ID, person_id):
            rds.sadd(CONTACTERS_ID, person_id)
        for k in focused_keys:
            info = {k: p.get(k, '').strip()}
            set_contacter(person_id, **info)
