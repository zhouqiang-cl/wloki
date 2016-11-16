 #-*- coding: utf-8 -*-

import re
from collections import defaultdict
from sqlalchemy.exc import IntegrityError
from decimal import Decimal as D  # NOQA
from torext import params

from .. import errors
from ..base.handlers import APIHandler
from .models import (get_bind_tpl, get_available_tpl, search_grp, create_grp,
                     search_tpl, bind_tpl_to_grp, search_tpl, delete_tpl_from_grp,
                     get_name_by_id, get_id_by_template, inherit_template, delete_tpl)
from ..privilege import require_node_privileges
from .privileges import MonitorRelativesPrivilege


class MonitorTemplatesHandler(APIHandler):
    def get(self):
        _type = self.get_argument('type', "template")
        grp_id = self.get_argument('grp_id', None)

        data = []
        if _type == "template":
            data =  get_bind_tpl(grp_id)
        elif _type == "available":
            data = get_available_tpl(grp_id)

        self.write_data(data)


class MonitorRelativesHandler(APIHandler):
    @require_node_privileges(MonitorRelativesPrivilege.manage_relatives, lambda c: int(c.args[0]))
    @params.simple_params(datatype="json")
    def put(self, grp_id):
        templates = self.params['templates']

        if search_grp(grp_id) == False:
            grp_name = get_name_by_id(grp_id)
            create_grp(grp_id, grp_name)
    
        current_user = self.user.username
        tpl_ids = get_id_by_template(templates)
        new_ids = inherit_template(current_user, grp_id, tpl_ids)
        bind_tpl_to_grp(grp_id, new_ids)

        data = {
            "status": True, 
            "message": "bind {0} to {1} succeed".format(templates, grp_id)
        }
        self.write_data(data)

    @require_node_privileges(MonitorRelativesPrivilege.manage_relatives, lambda c: int(c.args[0]))
    @params.simple_params(datatype="json")
    def delete(self, grp_id):
        templates = self.params['templates']

        tpl_ids = get_id_by_template(templates)
        #delete_tpl_from_grp(grp_id, tpl_ids)
        delete_tpl(tpl_ids)

        data = {
            "status": True, 
            "message": "unbind {0} from {1} succeed".format(templates, grp_id)
        }
        self.write_data(data)


handlers = [
    ('/relatives/(\d+)/templates', MonitorRelativesHandler),
    ('/templates', MonitorTemplatesHandler)
]
