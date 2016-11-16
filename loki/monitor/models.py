#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import requests
from .. import errors
from ..node.nodes import TreeNode


falcon_portal_addr = "http://falcon-portal.internal.nosa.me"
falcon_internal_addr = "http://falcon-portal.nosa.me/template/view/"
headers = {'X-Falcon-Token': 'token:Umn7BhILxJfsPNCzGYID0swJKFPQPm41'}


def get_bind_tpl(grp_id):
    url = falcon_portal_addr + "/api/group/templates/" + str(grp_id)
    r = requests.get(url, headers=headers)

    data = []
    if isinstance(r.json()['msg'], list):
        for item in r.json()['msg']:
            data.append(
                {
                    "template": link_proc(item['name'])
                })
    return data


def get_available_tpl(grp_id):
    url = falcon_portal_addr + "/api/templates"
    r = requests.get(url, headers=headers)

    data = []
    for item in r.json()['msg']:
        if re.match('i_[0-9]+', item['name']):continue
        grp_ids = get_bind_grp(item['id'])
        data.append({
                "template": link_proc(item['name']),
                "ids": grp_ids
            })

    return data

def link_proc(tpl_name):
    tpl_names = []
    tpl_names.append(tpl_name)
    tpl_id = get_id_by_template(tpl_names)[0]
    link = '<a href=' + '"' + falcon_internal_addr + str(tpl_id) + '">' + str(tpl_name) + '</a>'

    return str(link)


def get_bind_grp(tpl_id):
    url = falcon_portal_addr + "/api/template/binds/" + str(tpl_id)
    r = requests.get(url, headers=headers)

    data = []
    for item in r.json()['msg']:
        data.append(item['id'])
    return data


def search_grp(grp_id):
    url = falcon_portal_addr + "/api/group/view?grp_id=" + str(grp_id)
    r = requests.get(url, headers=headers)
    
    return len(r.json()['msg']) != 0


def create_grp(grp_id, grp_name):
    url = falcon_portal_addr + "/api/group/create?grp_id={0}&grp_name={1}".format(grp_id, grp_name)
    r = requests.get(url, headers=headers)

    return r.json()['msg'] == ''


def search_tpl(value):
    pass


def bind_tpl_to_grp(grp_id, tpl_ids):
    for tpl_id in tpl_ids:
        url = falcon_portal_addr + "/api/group/bind/template?grp_id={0}&tpl_id={1}".format(grp_id, tpl_id)
        requests.get(url, headers=headers)


def delete_tpl_from_grp(grp_id, tpl_ids):
    for tpl_id in tpl_ids:
        url = falcon_portal_addr + "/api/group/unbind/template?grp_id={0}&tpl_id={1}".format(grp_id, tpl_id)
        requests.get(url, headers=headers)


def delete_tpl(tpl_ids):
    for tpl_id in tpl_ids:
        url = falcon_portal_addr + "/api/template/delete/" + str(tpl_id)
        requests.get(url, headers=headers)


def get_name_by_id(grp_id):
    if grp_id is not None:
        node = TreeNode(int(grp_id), with_path=True)
    else:
        raise errors.ValidationError("node_id or path argument is required")

    return node.path.encode('utf8')


def get_id_by_template(tpl_names):
    #urls = [ falcon_portal_addr + "/api/template/view?tpl_name=" + name for name in tpl_names ]
    ids = []
    for name in tpl_names:
        if re.search('<|>', name):
            name = name.split('>')[1].split('<')[0]
        url = falcon_portal_addr + "/api/template/view?tpl_name=" + name
        r = requests.get(url, headers=headers)
        ids.append(r.json()['msg'][0]['id'])

    return ids


def inherit_template(user, grp_id, tpl_ids):
    suffix = str(grp_id)
    owner = user

    new_ids = []
    for tpl_id in tpl_ids:
        url = falcon_portal_addr + "/api/template/inherit/" + str(tpl_id) + "?suffix={0}&owner={1}".format(suffix, owner)
        r = requests.get(url, headers=headers)
        new_ids.append(r.json()['id'])

    return new_ids
