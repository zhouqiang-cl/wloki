# -*- coding: utf-8 -*-

import ldap
import logging
import requests

from .app import settings


def ldap_auth(username, password):
    dn = 'uid=%s,ou=People,dc=nosajia,dc=com' % username
    ldapconn = ldap.initialize('ldap://%s' % settings.LDAP_HOST)
    try:
        ldapconn.simple_bind_s(dn, password)
        return True
    except ldap.INVALID_CREDENTIALS:
        logging.debug('LDAP Auth failed: INVALID_CREDENTIALS')
        return False
    #except Exception as e:
        #print type(e), e.__class__, e
    finally:
        ldapconn.unbind()


class LoginException(Exception):

    '''my defined login exception'''

    def __init__(self, data):
        Exception.__init__(self, data)
        self.__data = data

    def __str__(self):
        return str(self.__data)


class AuthHelper(object):
    logging_info = {}

    def __init__(self,
                 username,
                 password,
                 auth_url,
                 username_key="username",
                 password_key="password"):
        self.username = username
        self.username_key = username_key
        self.password = password
        self.password_key = password_key
        self.auth_url = auth_url
        self._auth()

    def _auth(self, force=False):
        if force or not AuthHelper.logging_info.get('cookies', None):
            post_body = {
                self.password_key: self.password,
                self.username_key: self.username
            }
            r = requests.post(self.auth_url, post_body)
            if r.status_code != 200:
                raise LoginException("login Fail, can't get authenticated cookies")
            AuthHelper.logging_info.update({'cookies': r.cookies})

    def get(self, url, **kwargs):
        r = requests.get(url, cookies=AuthHelper.logging_info['cookies'], **kwargs)
        if r.status_code > 300:
            self._auth(force=True)
            r = requests.get(url, cookies=AuthHelper.logging_info['cookies'], **kwargs)
        return r

    def post(self, url, **kwargs):
        r = requests.post(url, cookies=AuthHelper.logging_info['cookies'], **kwargs)
        if r.status_code > 300:
            self._auth(force=True)
            r = requests.post(url, cookies=AuthHelper.logging_info['cookies'], **kwargs)
        return r
