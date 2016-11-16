#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..base.handlers import BaseHandler
from .conf import (
    CHART_CONFIGS,
    HTTP_CONFIGS,
    DOMAIN_CONFIGS,
    USAGE_CONFIGS,
    AVAILABILITY_CONFIGS,
)


class ConfigsHandler(BaseHandler):
    def get(self):
        self.write_data(CHART_CONFIGS)


class HTTPConfigsHandler(BaseHandler):
    def get(self):
        self.write_data(HTTP_CONFIGS)
        self.finish()


class DomainConfigsHandler(BaseHandler):
    def get(self):
        self.write_data(DOMAIN_CONFIGS)
        self.finish()


class UsageConfigsHandler(BaseHandler):
    def get(self):
        self.write_data(USAGE_CONFIGS)
        self.finish()


class AvailabilityConfigsHandler(BaseHandler):
    def get(self):
        self.write_data(AVAILABILITY_CONFIGS)
        self.finish()


handlers = [
    ('/configs', ConfigsHandler),
    ('/http_configs', HTTPConfigsHandler),
    ('/domain_configs', DomainConfigsHandler),
    ('/usage_configs', UsageConfigsHandler),
    ('/availability_configs', AvailabilityConfigsHandler),
]
