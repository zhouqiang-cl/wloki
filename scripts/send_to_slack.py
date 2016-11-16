#!/usr/bin/env python
# coding: utf-8

import requests

payload_template = '{{"channel": "#{channel}", "username": "deploybot", "text": "'
text_sections = [
    '*{job_name}*\\t`{before_status}` → `{current_status}`\\t[{updated_at}]\\t',
    '>发布人:  {creator}\\t[{created_at}]',
    '>节点　:  <http://loki.nosa.me/job?nid={node_id}|{node_path}>',
    '>ID　　:  <http://loki.nosa.me/job?nid=2911&tab=3&rid={job_id}|{job_id}>',
]
payload_template += '\\n'.join(text_sections)
payload_template += '", "icon_emoji": ":rocket:"}}'
print payload_template

payload = payload_template.format(
    channel='slack-test',
    #channel='sre-team',
    job_name='【线上】发布ripple-webapp',
    job_id='7951440489782259404',
    node_id=2911,
    creator='mengxiao',
    node_path='/nosajia/sre/package-search',
    current_status='success',
    before_status='doing',
    created_at='2015-08-25 17:00',
    updated_at='2015-08-25 17:20',
)
print payload


r = requests.post(
    url="https://hooks.slack.com/services/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",
    #url='https://hooks.slack.com/services/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',
    data=payload,
)
print('Response HTTP Status Code   : {status_code}'.format(status_code=r.status_code))
print('Response HTTP Response Body : {content}'.format(content=r.content))
