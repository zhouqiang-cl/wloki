#!/usr/bin/env python
# -*- coding:utf-8 -*-

__author__ = 'qinguoan@nosa.me,zhouqiang@nosa.me'

import re
import os
import sys
import socket
import smtplib
import json
import urllib
import urllib2
import time
from loki.tsdb import OpenTSDB


def AGG(total,data):
    done = 0
    for domain in total:
        for p in sorted(total[domain].iteritems(), key=lambda a:a[0].count('/'), reverse = True):
            path = p[0]
            if path == '/' or path == "TOTAL":continue
            num = total[domain][path]
            newpath = re.sub('/[\w\.]*[^/]$', '', path)
            if num < 100000:
                if not newpath:newpath = '/'
                if newpath in total[domain]:
                    total[domain][newpath] += num
                    for code in data[domain][path]:
                        if code not in data[domain][newpath]:
                            data[domain][newpath][code] = dict()
                            data[domain][newpath][code]['num'] = 0
                        data[domain][newpath][code]['num'] += data[domain][path][code]['num']
                else:
                    data[domain][newpath] = data[domain][path]
                    total[domain][newpath] = num
                del total[domain][path]
                del data[domain][path]
                done += 1
            else:
                if not newpath:continue
                if newpath in total[domain]:
                    total[domain][newpath] += num
                    for code in data[domain][path]:
                        if code not in data[domain][newpath]:
                            data[domain][newpath][code] = dict()
                            data[domain][newpath][code]['num'] = 0
                        data[domain][newpath][code]['num'] += data[domain][path][code]['num']
                    del total[domain][path]
                    del data[domain][path]
                    done += 1
    if done > 0:
        AGG(total,data)

    return [ total, data ]


def main():
    tsdb = OpenTSDB()
    data = dict()
    total = dict()
    body = ""
    CURPATH = os.path.dirname(os.path.abspath(__file__))
    white_list = CURPATH+'/../conf/whitelist'
    if os.path.isfile(white_list):
        white_domain = [ d for d in open(white_list, 'r').read().split('\n') if d ]
    else:
        white_domain = []
    for line in open(sys.argv[1], 'r'):
        fields = line.split()
        if len(fields) < 4:continue
        domain, code, path, num = fields[0], fields[1], fields[2].split('?')[0], fields[-1]
        #if not re.search('^\d+', code):continue
        if re.search('\D+', code):continue
        if int(code) >= 600 or int(code) < 200:continue
        if white_domain and domain not in white_domain:continue
        if domain not in data: data[domain] = dict()
        if domain not in total: total[domain] = dict()
        while re.search('/?https?://.*?/',path):
            path = re.sub('/?https?://.*?/','/',path)
        try:
            path = re.sub('//','/',path)

            if path != '/':
                uris = [ p for p in path.split('/') if p ]
                path = ''
                l = 2 if len(uris) > 3 else 1
                for i in xrange(l):
                    if (len(uris[i])>20):
                        uris[i] = '*'
                    path += '/' + uris[i]
                path = '/' + path
        except Exception,e:
            print "exception: ", line, e
        if re.match('//', path):
            path = re.sub('^/', '', path,1)
        path = path.replace('.', '-')
        if path not in data[domain]:
            data[domain][path] = dict()

        if path not in total[domain]:
            total[domain][path] = int(num)
        else:
            total[domain][path] += int(num)

        if code in data[domain][path]:
            data[domain][path][code]['num'] += int(num)
        else:
            data[domain][path][code] = dict()
            data[domain][path][code]['num'] = int(num)
    #合并数据
    total, data = AGG(total, data)
    timestamp = (int(time.time())/86400-1)*86400
    for domain in data:
        for path in data[domain].keys():
            total_num = total[domain][path]
            codes = data[domain][path].keys()
            postval = list()
            for code in codes:
                num = data[domain][path][code]['num']
                pct = data[domain][path][code]['pct'] = "%.2f%%" % \
                    ( float(num) * 100/ total_num )
                tsdbdata = dict()
                tsdbdata['metric'] = "domain.detail.daily"
                tsdbdata['timestamp'] = timestamp
                tsdbdata['value'] = num
                tsdbdata['tags'] = dict()
                tsdbdata['tags']['code'] = code
                tsdbdata['tags']['uri'] = path.strip('*')
                tsdbdata['tags']['type'] = 'num'
                postval.append(tsdbdata)
        try:
            tsdb.send(postval)
        except Exception as e:
            print str(e)


if __name__ == "__main__":
    main()
