#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import time
from loki.node.nodes import TreeNode
import requests
import ujson as json
import gevent
from blinker import Signal

from loki.app import mail, settings
from loki.mail import Message
from loki.job.statuses import Status
from loki.utils import catch_exception

# for deployment
on_status_changed = Signal()

logger = logging.getLogger("signals.deploy")

SLACK_WEB_HOOK = "http://slack-proxy.hy01.internal.nosa.me/post"


@on_status_changed.connect
@catch_exception(logger)
def send_mail(sender, operator=None, **kwargs):
    """
    :param sender: job.models.Deployment
    """
    logger.debug("catch status changed signal for send_mail")
    status = Status(sender.status).name \
        if sender.status != Status.unknown \
        else "started"
    recipients = sender.parameters['contacters'] + ["ep-robots@nosa.me"]
    msg = Message(u'[SRE] 发布 "%s"' % sender.name, body=status, sender="work@nosa.me",
                  recipients=recipients)
    if not settings.DEBUG:
        mail.send(msg)
        logger.info("send %s status changed mail to %s" % (sender.name, recipients))
    else:
        logger.warn("[DEBUG SKIP SIGNAL] send %s status changed mail to %s" % (sender.name, recipients))


@on_status_changed.connect
@catch_exception(logger)
def send_slack_msg(sender, operator=None, **kwargs):
    """
    :param sender: job.models.Deployment
    """
    logger.debug("catch status changed signal for send_loki_msg")
    status = Status(sender.status).name \
        if sender.status != Status.unknown \
        else "started"
    if operator:
        message = u"状态变更 %s by %s" % (status, operator)
    else:
        message = u"状态变更 %s" % status

    msg = {
        "node_name": TreeNode(sender.node_id).path,
        "deploy_name": sender.name,
        "message": message,
        "url": "{}job?nid={:d}&tab=3&rid={:d}".format(settings.PUBLIC_DOMAIN,
                                                      sender.node_id,
                                                      sender.id),
        "ctime": int(time.mktime(sender.ctime.timetuple())),
        "mtime": int(time.mktime(sender.mtime.timetuple())),
    }
    if not settings.DEBUG:
        gevent.spawn(requests.post, SLACK_WEB_HOOK, data=json.dumps(msg, ensure_ascii=False))
        logger.info("send slack_msg %s async" % msg['message'])
    else:
        logger.warn("[DEBUG SKIP SIGNAL] send slack_msg %s async" % msg['message'])
