# -*- coding: utf-8 -*-

from ..app import settings
# from ..base import models


class User(object):
    def __init__(self, username):
        self.username = username
        self.signature = username.upper()
        self.id = username

    @classmethod
    def get(cls, username):
        return cls(username)

    def get_group(self):
        for group, users in settings['GROUPS'].iteritems():
            for u in users:
                if u == self.username:
                    return group
        return None

    def get_accessible_nodes(self):
        # TODO replace with new authentication mechanism
        return [1]

    def has_perm(self, uri):
        pass
