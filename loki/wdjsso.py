#!/usr/bin/env python
# coding: utf-8


"""
{
    "function": "Engineering Productivity",
    "school": "NanXiang",
    "name": "UserName",
    "img": "http://who.nosa.me/static/img/mengxiao.jpg",
    "socials": [
        {
            "type": "twitter",
            "val": "https://twitter.com/123"
        },
        {
            "type": "github",
            "val": "https://github.com/123"
        }
    ],
    "hometown": "Mars",
    "ladder": "SA",
    "sex": "男",
    "phone": "18888888888",
    "manager": {...},
    "location": "A111",
    "xingzuo": "ChuNv",
    "objective": "SRE, Python, Web",
    "mail": "username@nosa.me",
    "type": "person",
    "id": "username",
    "edate": "2014-02-21"
}
"""

from __future__ import absolute_import
from Crypto.Cipher import AES
import redis

AES_KEY = b'2i3v7g23v8n329nc'
AES_IV = b'gd93m9c5sc3eich3'
REDIS_IP = "10.19.29.148"
REDIS_PORT = 6379

def get_user_by_sessionid(sessionKey):
    try:
        redisHandler = redis.StrictRedis(host=REDIS_IP, port=REDIS_PORT)
        if not sessionKey:
            raise AssertionError()
        responese = redisHandler.get(sessionKey)
        decryptor = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
        plain = decryptor.decrypt(responese)
        return plain.rstrip('\0')
    except:
        # 没登陆
        return None


def get_login_address(redirect):
    return "https://sso.nosa.me/?redirect=%s" % redirect


def get_logout_address(redirect):
    return "https://sso.nosa.me/logout/?redirect=%s" % redirect
