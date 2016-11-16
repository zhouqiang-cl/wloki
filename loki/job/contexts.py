#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum


class Context(Enum):
    template_form = 1
    deploy_form = 2
    dashboard_form = 3

context_universal_set = set(Context.__members__.values())
