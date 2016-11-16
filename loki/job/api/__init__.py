#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .. import templates
from . import template, deploy

handlers = template.handlers + deploy.handlers
