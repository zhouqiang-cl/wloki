#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import IntEnum


class Status(IntEnum):
    unknown = 0
    doing = 1
    stopped = 6
    error = 7
    succ = 8
    fail = 9


finished_statuses = {int(i) for i in (
    Status.stopped,
    Status.error,
    Status.succ,
    Status.fail
)}

unfinished_statuses = {int(i) for i in (
    Status.unknown,
    Status.doing
)}
