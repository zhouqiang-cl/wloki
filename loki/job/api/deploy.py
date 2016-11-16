#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import ujson as json

from gevent.event import AsyncResult
from kazoo.protocol.states import EventType
from loki.job.base import JobTemplate
from loki.job.templates.deleted_template import DeletedTemplate
from torext import params
from pbrpc.utils import RpcException

from ..models import Template
from ..models import Deployment
from loki.job.statuses import Status, finished_statuses, unfinished_statuses
from loki.signals import deploy as deploy_signals
from ...zookeeper import zk, NoNodeError
from ...base.template import get_template_by_type
from ...base.handlers import APIHandler
from ...errors import ParamsInvalidError, ValidationError, DoesNotExist, OperationNotAllowed, TemporaryServerError
from ...settings import ZK_JOB_STATUS_PATH, ZK_GANGR_PATH
from ...rpc import get_rpc_service
from ...privilege import require_node_privileges
from ..privileges import JobPrivilege
from loki.privilege.models import authorize


class TemplateParams(params.ParamSet):
    __datatype__ = 'json'

    type = params.Field(required=True)
    parameters = params.Field(required=True)


class DeployLogHandler(APIHandler):
    def get(self):
        tid = self.get_argument("tid")
        hostname = self.get_argument("hostname")
        job_log_path = os.path.join(ZK_JOB_STATUS_PATH, tid, hostname)
        try:
            data, stats = zk.get(job_log_path)
        except NoNodeError:
            raise DoesNotExist("server %s deploy log doesn't exists" % hostname)
        self.write_data(data)


class DeployStatusHandler(APIHandler):
    def get(self):
        def watcher(event):
            if event.type in (EventType.CREATED, EventType.CHANGED):
                _data, _stats = zk.get(job_status_path)
                async_result.set((_data, _stats))

        tid = self.get_argument("tid")
        version = int(self.get_argument("version", -1))
        job_status_path = os.path.join(ZK_JOB_STATUS_PATH, tid)
        try:
            raw_data, stats = zk.get(job_status_path)
        except NoNodeError:
            raise DoesNotExist("job status doesn't exists")

        if version > stats.version:
            raise ValidationError("job status version too large")
        elif version == stats.version:
            async_result = AsyncResult()
            zk.exists(job_status_path, watch=watcher)
            raw_data, stats = async_result.get()

        try:
            data = json.loads(raw_data)
            # for compatible with 'undo' status set by GANGR
            # regard this as common unfinished status like 'unknown','doing' and ignore it
            if data['status'] == 'undo':
                pass
            elif Status[data['status']] in finished_statuses:
                Deployment.set_status(tid, Status[data['status']])
        except Exception as e:
            Deployment.set_status(tid, Status.error)
            raise TemporaryServerError("fetched status illegal: %s" % e)

        ret = {
            "version": stats.version,
            "data": data,
        }
        self.write_json(ret)


class DeployTypeHandler(APIHandler):
    require_auth = True

    # @profile(sort="cumtime", lines=100)
    def get(self):
        node_id = int(self.get_argument("node_id", None))
        if not node_id:
            raise ParamsInvalidError("node_id is needed")
        data = []
        for t in Template.query.filter_by(node_id=node_id).all():
            try:
                template_cls = get_template_by_type(t.type)
            except KeyError:
                template_cls = DeletedTemplate

            template = template_cls(**t.parameters)
            template.node_id = node_id
            d = {
                "template_id": t.id,
                "template_name": t.name,
                "template_type": t.type,
            }
            d["parameters"] = template.render_deploy_form()
            data.append(d)
        self.write_data(data)


def authorize_deployment_privilege(privilege, username, deploy):
    authorize(privilege, username, node_id=deploy.node_id)


class DeployHandler(APIHandler):
    require_auth = True

    def get(self, tid):
        deploy = Deployment.query.get(int(tid))
        if not deploy:
            raise DoesNotExist("deployment %s not exists" % tid)

        d = {}
        try:
            template_cls = get_template_by_type(deploy.type)
        except KeyError:
            template_cls = DeletedTemplate

        template = template_cls(**deploy.parameters)
        d["parameters"] = template.render_dashboard_form()

        # for data compatibility
        if isinstance(template.servers[0], dict):
            d["servers"] = [s['key'] for s in template.servers if s['value']]
        else:
            d["servers"] = template.servers

        d["status"] = Status(deploy.status).name
        self.write_data(d)

    def delete(self, tid):
        deploy = Deployment.query.get(int(tid))
        if not deploy:
            raise DoesNotExist("deployment %s not exists" % tid)

        # authorize
        authorize_deployment_privilege(JobPrivilege.manage_deployment, self.user.username, deploy)

        deploy.delete()
        self.set_status(204)


class DeployListHandler(APIHandler):
    require_auth = True

    def get(self):
        node_id = self.get_argument("node_id", None)
        if not node_id:
            raise ParamsInvalidError("node_id is needed")
        node_id = int(node_id)

        deploys = Deployment.query.filter_by(node_id=node_id)\
                                  .order_by(Deployment.ctime.desc()).limit(50).all()

        data = [{
            "id": str(d.id),
            "name": d.name,
            "status": Status(d.status).name,
            "ctime": d.ctime.strftime("%Y-%m-%d %H:%M:%S")
        } for d in deploys]
        self.write_data(data)

    @require_node_privileges(JobPrivilege.manage_deployment,
                             lambda c: int(c.handler.get_argument('node_id')))
    @TemplateParams.validation_required
    def put(self):
        node_id = int(self.get_argument("node_id", None))
        if not node_id:
            raise ParamsInvalidError("node_id is needed")
        data = self.params.data

        try:
            template_model = Template.query.filter_by(node_id=node_id, name=data['parameters']['name']).one()
            try:
                template_cls = get_template_by_type(template_model.type)
            except KeyError:
                template_cls = DeletedTemplate
            template = template_cls(**template_model.parameters)
            deployment = JobTemplate.get_deployment_by_template(template, data['parameters'])
            deployment_model = deployment.generate_deployment_model()
            deployment_model.node_id = node_id
        except TypeError as e:
            raise ValidationError(str(e))

        try:
            if Deployment.query.filter((Deployment.node_id == node_id) &
                                       (Deployment.name == deployment.name) &
                                       (Deployment.status.in_(unfinished_statuses)))\
                    .with_for_update(read=True).first():
                raise OperationNotAllowed('there is a job for "%s" unfinished, status is %s' %
                                          (deployment_model.name,
                                           Status(deployment_model.status).name))
            deployment_model.save()
        finally:
            Deployment.rollback()

        try:
            deployment.send_deploy_request(node_id)
        except Exception:
            deployment_model.delete()
            raise
        deploy_signals.on_status_changed.send(deployment_model,
                                              operator=self.user.username)
        ret = {
            "jobset_id": str(deployment_model.id),
            "message": "create deploy succeed"
        }
        self.write_json(ret)


class ManageDeployHandler(APIHandler):
    require_auth = True

    def get(self, action, tid):
        tid = long(tid)
        deploy = Deployment.query.get(tid)
        if not deploy:
            raise DoesNotExist("deployment %s not exists" % tid)

        # authorize
        authorize_deployment_privilege(JobPrivilege.manage_deployment, self.user.username, deploy)

        data = {}
        try:
            service = get_rpc_service(ZK_GANGR_PATH)
            if action == 'pause':
                service.pause_job(tid)
            elif action == 'play':
                service.continue_job(tid)
            elif action == 'stop':
                service.stop_job(tid)
            else:
                raise ValidationError('wrong action to a job')
            data['status'] = True
        except RpcException:
            data['status'] = False
        self.write_json(data)


handlers = [
    ('/get_log', DeployLogHandler),
    ('/get_status', DeployStatusHandler),
    ('/deploy', DeployListHandler),
    ('/deploy/(\d+)', DeployHandler),
    ('/deploy/(pause|play|stop)/(\d+)', ManageDeployHandler),
    ('/deploy_type', DeployTypeHandler),
]
