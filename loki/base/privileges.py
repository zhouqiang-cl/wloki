#!/usr/bin/env python
# -*- coding: utf-8 -*-
import operator
from collections import namedtuple

import enum
from enum import Enum
from lazy_object_proxy.slots import Proxy
from sqlalchemy.util import classproperty

__all__ = ['get_privilege_by_name', 'PrivilegeBase', 'PrivilegeItem', 'PrivilegeGroup']

__all_privileges__ = {}


def get_privilege_by_name(name):
    return __all_privileges__[name]


def get_all_privileges_items():
    return __all_privileges__.viewitems()


PrivilegeItem = namedtuple("PrivilegeItem", ("name", "desc"), verbose=False)


class PrivilegeGroup(enum.Enum):
    normal = u"普通"
    critical = u"特殊"


class PrivilegeMeta(type):
    def __new__(mcs, cls_name, bases, dict_):
        name = dict_.get('__privilege_name__')
        if name in __all_privileges__:
            raise ValueError("{} have been registered, name conflicted".format(cls_name))

        privileges = {}

        """
        the least significant bit of privilege value represent its validity,
        other bits definition described in loki.privilege.models.PrivilegeStatus
        1: valid
        0: invalid
        """
        privilege_init_value = 0b0001

        privilege_order = [i.name for i in dict_['__privileges__']]

        if name:
            if 'admin' not in privilege_order:
                raise ValueError("{} attribute __privileges__ first position should been 'admin'"
                                 .format(cls_name))
            else:
                # reorder privilege_order
                privilege_order.remove("admin")
                privilege_order.append("admin")

        for privilege in dict_.get('__privileges__', ()):
            privileges[privilege.name] = {"value": privilege_init_value,
                                          "desc": privilege.desc}

            privilege_init_value <<= 4

        cls = type.__new__(mcs, cls_name, bases, dict_)

        for k, v in privileges.items():
            new_value = cls(v['value'], v['desc'])
            setattr(cls, k, new_value)
            privileges[k] = new_value

        privileges["__order__"] = " ".join(privilege_order)

        cls.__privilege_enum__ = type('PrivilegeEnum', (Enum,), privileges)

        if name:
            __all_privileges__[name] = cls
        return cls


class PrivilegeDescriptor(object):
    def __init__(self, init_value, desc):
        self.init_value = init_value
        self.desc = desc



class PrivilegeBase(object):
    __metaclass__ = PrivilegeMeta
    __privileges__ = tuple()
    # __privileges__ = (PrivilegeItem("admin", "..."),
    #                   PrivilegeItem("read", "..."),
    #                   PrivilegeItem("write", "..."))
    __privilege_name__ = None
    # __privilege_name__ = "basePrivilege"
    __privilege_alias__ = None

    def __init__(self, matrix=0b000, desc=None):
        self._desc = desc
        self._matrix = matrix

        init_value = 0b0001
        for p in self.__privileges__:
            setattr(self.__class__, "_%s" % p.name,
                    property(fget=self._create_fget(init_value),
                             fset=self._create_fset(init_value)))
            init_value <<= 4

    @staticmethod
    def _create_fset(init_value):
        def fset(self, value):
            lower_part = self._matrix % init_value
            higher_part = self._matrix - (self._matrix % (init_value * 0b10000))
            self._matrix = lower_part + higher_part + value * init_value

        return fset

    @staticmethod
    def _create_fget(init_value):
        return lambda self: (self._matrix / init_value) & 0b1111

    @property
    def desc(self):
        return self._desc

    @property
    def matrix(self):
        return self._matrix

    @classproperty
    def name(self):
        return self.__privilege_name__

    @classproperty
    def enum(self):
        return self.__privilege_enum__

    @classproperty
    def group(self):
        return self.__type__

    @classmethod
    def get_alias(cls):
        return cls.__privilege_alias__

    @property
    def privileges(self):
        return {p for p in self.enum.__members__.values() if p.value & self._matrix}

    def get_matrix_by_name(self, name):
        return getattr(self, "_%s" % name)

    def set_matrix_by_name(self, name, value):
        setattr(self, "_%s" % name, value)

    def __nonzero__(self):
        return self._matrix

    def __and__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(self._matrix & other._matrix)
        elif isinstance(other, int):
            return self.__class__(self._matrix & other)
        else:
            raise NotImplementedError

    def __or__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(self.matrix | other.matrix)
        elif isinstance(other, int):
            return self.__class__(self.matrix | other)
        else:
            raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.matrix == other.matrix
        elif isinstance(other, int):
            return self.matrix == other
        else:
            raise NotImplementedError

    def __hash__(self):
        return hash(self._matrix)

    def __str__(self):
        return repr(self)

    def __unicode__(self):
        return unicode(repr(self))

    def __repr__(self):
        if len(self.privileges) == 0:
            return "<{}: {}>".format(self.name, None)
        elif len(self.privileges) == 1:
            return "<{}: {}>".format(
                self.name, self.enum(self.matrix).name)
        else:
            return "<{}: {}>".format(
                self.name, ", ".join(
                    [self.enum(p.value.matrix).name for p in self.privileges]
                ))


# if __name__ == "__main__":
#     print PrivilegeBase.enum
#     print PrivilegeBase.read == PrivilegeBase.write
#     print PrivilegeBase.read | PrivilegeBase.write
#     print PrivilegeBase.read & PrivilegeBase.write
#     p = PrivilegeBase(0b000111000)
#     print p.read
#     print p.write
#     print p.admin
