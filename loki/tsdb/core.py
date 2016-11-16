# -*- coding: utf-8 -*-

import json
import traceback
import logging

from ..app import settings
from ..utils import asyncrequest
from ..errors import RequestError
from ..db import get_redis


KEY_PREFIX = settings.OPENTSDB_CACHE_KEY_PREFIX


def tsdb_query(uri, typ='default', cache=True, cache_ttl=settings.OPENTSDB_CACHE_TTL):
    tsdb_uri = uri[5:]
    url = '%s%s' % (settings.OPENTSDB_URL, tsdb_uri)

    # set expire time to 12 hours for the fucking url.bandwidth query
    if 'url.bandwidth' in url:
        logging.info('I see the fucking url.bandwidth')
        cache_ttl = 60 * 60 * 12

    if cache:
        cache_key = KEY_PREFIX + tsdb_uri
        cache_rds = get_redis(db=settings.REDIS_DB_FOR_CACHE)
        raw_rv = cache_rds.get(cache_key)
        print 'Get from cache'
        if not raw_rv:
            print 'Not in cache'
            # Doing normal request
            raw_rv = _tsdb_request(url)

            pipe = cache_rds.pipeline()
            print 'set redis', cache_key
            pipe.set(cache_key, raw_rv)
            pipe.expire(cache_key, cache_ttl)
            pipe.execute()
    else:
        raw_rv = _tsdb_request(url)

    rv = json.loads(raw_rv)
    return rv


def _tsdb_request(url):
    try:
        resp = asyncrequest('GET', url, timeout=settings.OPENTSDB_TIMEOUT)
    except Exception, e:
        raise RequestError(str(e))
    if resp.status_code != 200:
        traceback.print_exc()
        raise RequestError(resp.content)
    return resp.content
