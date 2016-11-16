#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..utils import _to_float3
from ..zookeeper import zk
from .. import errors


def highcharts(raw, typ='default', network=False):

    if 'default' == typ:
        return [dict(
            name=str('{%s}' % (','.join(map(lambda x: '='.join(x),
                m['tags'].iteritems())))),
            data=sorted([[int(p[0]) * 1000, _to_float3(p[1])]
                         for p in m['dps'].items()], key=lambda x:x[0]),
        ) for m in raw]

    elif 'system' == typ:
        result = []
        for m in raw:
            if 'mount' in m['tags']:
                result.append(dict(
                    name=str('%s:%s' % (m['tags']['endpoint'], m['tags']['mount'])),
                    data=sorted([[int(p[0]) * 1000, _to_float3(p[1])]
                         for p in m['dps'].items()], key=lambda x:x[0]),
                ))
            elif 'device' in m['tags']:
                result.append(dict(
                    name=str('%s:%s' % (m['tags']['endpoint'], m['tags']['device'])),
                    data=sorted([[int(p[0]) * 1000, _to_float3(p[1])]
                         for p in m['dps'].items()], key=lambda x:x[0]),
                ))
            else:
                result.append(dict(
                    name=str('%s' % (m['tags']['endpoint'])),
                    data=sorted([[int(p[0]) * 1000, _to_float3(p[1])]
                         for p in m['dps'].items()], key=lambda x:x[0]),
                ))

        return result

    elif 'http' == typ:
        series = [dict(
            name=str('%s' % _construct_url(m['tags'])),
            data=sorted([[int(p[0]) * 1000, _to_float3(p[1])]
                         for p in m['dps'].items()], key=lambda x:x[0]),
        ) for m in raw]
        return series

    elif 'domain' == typ:
        series = [dict(
            name=str('%s' % m['tags']['path']),
            data=sorted([[int(p[0]) * 1000, _to_float3(p[1])]
                         for p in m['dps'].items()], key=lambda x:x[0]),
        ) for m in raw]
        return [s for s in series if s['data']]

    elif 'peity' == typ:
        return map(lambda p: _to_float3(p[1]),
                   sorted(raw[0]['dps'].iteritems(),
                          key=lambda p: p[0]))

    elif 'product' == typ:
        return [dict(
            name=str('%s' % zk.without_expire.get_node_name(m['tags']['nodeid'])),
            data=sorted([[int(p[0]) * 1000, _to_float3(p[1])]
                         for p in m['dps'].items()], key=lambda x:x[0]),
        ) for m in raw]

    else:
        raise errors.ParamsInvalidError('Invalid param type: %s' % typ)


def _construct_url(tags):
    url = ''
    if 'domain' in tags:
        url += tags['domain']
    if 'path' in tags:
        url += tags['path']
    return url
