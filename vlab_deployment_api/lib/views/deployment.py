# -*- coding: UTF-8 -*-
"""
Defines the HTTP API for working with deployments in vLab.
"""
import ujson
from flask import current_app
from flask_classy import request, route, Response
from vlab_inf_common.views import MachineView
from vlab_inf_common.vmware import vCenter, vim
from vlab_api_common import describe, get_logger, requires, validate_input


from vlab_deployment_api.lib import const


logger = get_logger(__name__, loglevel=const.VLAB_DEPLOYMENT_LOG_LEVEL)


class DeploymentView(MachineView):
    """API end points for vLab deployments"""
    route_base = '/api/2/inf/deployment'
    RESOURCE = 'deployment'
    POST_SCHEMA = { "$schema": "http://json-schema.org/draft-04/schema#",
                    "type": "object",
                    "description": "Create a deployment",
                    "properties": {
                        "template": {
                            "description": "The name for a set of images that make up a deployment.",
                            "type": "string"
                        }
                    },
                    "required": ["template"]
                  }
    DELETE_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                     "description": "Destroy a Deployment",
                     "type": "object",
                     "properties": {
                        "template": {
                            "description": "The template name of the deployment instance to destroy",
                            "type": "string"
                        }
                     },
                     "required": ["template"]
                    }
    GET_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                  "description": "Display the Deployment instances you own"
                 }
    TEMPLATES_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                        "description": "View available versions of Deployment that can be created",
                        "type": "object",
                        "properties" : {
                            "verbose": {
                                "description": "Include extra details about the images/templates available for deployment.",
                                "type": "boolean",
                                "default": False,
                            }
                        }
                       }


    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @describe(post=POST_SCHEMA, delete=DELETE_SCHEMA, get=GET_SCHEMA)
    def get(self, *args, **kwargs):
        """Display information about your deployment"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        txn_id = request.headers.get('X-REQUEST-ID', 'noId')
        task = current_app.celery_app.send_task('deployment.show', [username, txn_id])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @validate_input(schema=POST_SCHEMA)
    def post(self, *args, **kwargs):
        """Create a Deployment"""
        user_token = request.headers.get('X-Auth')
        username = kwargs['token']['username'] # the 'token' in kwargs is a usable object. The header is just a JWT string.
        resp_data = {'user' : username}
        txn_id = request.headers.get('X-REQUEST-ID', 'noId')
        body = kwargs['body']
        template = body['template']
        client_ip = kwargs['token']['client_ip']
        task = current_app.celery_app.send_task('deployment.create', [username, user_token, template, client_ip, txn_id])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @validate_input(schema=DELETE_SCHEMA)
    def delete(self, *args, **kwargs):
        """Destroy a Deployment"""
        user_token = request.headers.get('X-Auth')
        username = kwargs['token']['username']
        txn_id = request.headers.get('X-REQUEST-ID', 'noId')
        resp_data = {'user' : username}
        template = kwargs['body']['template']
        client_ip = kwargs['token']['client_ip']
        task = current_app.celery_app.send_task('deployment.delete', [username, user_token, template, client_ip, txn_id])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @route('/image', methods=["GET"])
    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @describe(get_args=TEMPLATES_SCHEMA)
    def images(self, *args, **kwargs):
        """Show available versions of Deployment that can be deployed"""
        username = kwargs['token']['username']
        verbose = request.args.get('verbose', '')
        if verbose:
            if verbose.lower().startswith('t') or verbose.startswith('1'):
                verbose = True
        else:
            verbose = False
        txn_id = request.headers.get('X-REQUEST-ID', 'noId')
        resp_data = {'user' : username}
        task = current_app.celery_app.send_task('deployment.images', [verbose, txn_id])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp


class TemplateView(MachineView):
    """API end points for vLab deployment templates"""
    route_base = '/api/2/inf/template'
    RESOURCE = 'deployment'
    POST_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                    "type": "object",
                    "description": "Create a deployment",
                    "properties": {
                        "machines": {
                            "description": "The names of the machines that make up the template.",
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                        },
                        "name" : {
                            "description": "What to call the new template.",
                            "type": "string",
                            "pattern" : "^[A-Za-z0-9_-]+$"
                        },
                        "summary": {
                            "description": "A short description of the template",
                            "type": "string",
                            "maxLength" : 500,
                        },
                        "portmaps" : {
                            "description": "The NAT port forwarding rules to create.",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties" : {
                                    "name": {
                                        "type": "string",
                                        "description": "The name of the machine"
                                    },
                                    "target_addr": {
                                        "description": "The IP of the machine in your lab to connect to",
                                        "type": "string",
                                        "format": "ipv4"
                                    },
                                    "target_ports": {
                                        "description": "The port number(s) of the machine in your lab to connect to",
                                        "type": "array",
                                        "items": {
                                            "type": "integer",
                                            "minItems": 1,
                                        },
                                    },
                                },
                                "required" : ["name", "target_addr", "target_ports"]
                            }
                        }
                    },
                    "required" : ["name", "machines", "portmaps", "summary"]
                   }
    DELETE_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                     "description": "Destroy a Deployment",
                     "type": "object",
                     "properties": {
                        "template": {
                            "description": "The name of the deployment template instance to destroy",
                            "type": "string"
                        }
                     },
                     "required": ["template"]
                    }
    GET_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                  "description": "Display the Deployment instances you own"
                 }
    PUT_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                  "description": "Update the summary and/or owner of a template.",
                  "type": "object",
                  "properties": {
                    "owner" : {
                        "description": "The name of the new owner of a template",
                        "type": "string"
                    },
                    "summary": {
                        "description": "A short description of the template",
                        "type": "string",
                        "maxLength" : 500,
                    },
                    "template": {
                        "description": "The name of the template to modify",
                        "type": "string"
                    }
                  },
                  "anyOf": [
                    {"required": ['template', 'owner']},
                    {"required": ['template', 'summary']},
                    {"required": ['template', 'summary', 'owner']},
                  ]
                 }

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @describe(post=POST_SCHEMA, delete=DELETE_SCHEMA, get=GET_SCHEMA)
    def get(self, *args, **kwargs):
        """Display information about templates you own"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        txn_id = request.headers.get('X-REQUEST-ID', 'noId')
        task = current_app.celery_app.send_task('deployment.show_template', [username, txn_id])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @validate_input(schema=POST_SCHEMA)
    def post(self, *args, **kwargs):
        """Create a template"""
        username = kwargs['token']['username']
        machines = kwargs['body']['machines']
        portmaps = kwargs['body']['portmaps']
        summary = kwargs['body']['summary']
        template = kwargs['body']['name']
        resp_data = {'user' : username}
        txn_id = request.headers.get('X-REQUEST-ID', 'noId')
        body = kwargs['body']
        task = current_app.celery_app.send_task('deployment.create_template', [username, template, machines, portmaps, summary, txn_id])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @validate_input(schema=DELETE_SCHEMA)
    def delete(self, *args, **kwargs):
        """Destroy a template"""
        username = kwargs['token']['username']
        txn_id = request.headers.get('X-REQUEST-ID', 'noId')
        resp_data = {'user' : username}
        template = kwargs['body']['template']
        task = current_app.celery_app.send_task('deployment.delete_template', [username, template, txn_id])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @validate_input(schema=PUT_SCHEMA)
    def put(self, *args, **kwargs):
        """Modify a template"""
        username = kwargs['token']['username']
        txn_id = request.headers.get('X-REQUEST-ID', 'noId')
        resp_data = {'user' : username}
        template = kwargs['body']['template']
        summary = kwargs['body'].get('summary', '')
        owner = kwargs['body'].get('owner', '')
        task = current_app.celery_app.send_task('deployment.modify_template', [username, template, summary, owner, txn_id])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp
