# -*- coding: UTF-8 -*-
"""
Entry point logic for available backend worker tasks
"""
from celery import Celery
from requests.exceptions import RequestException
from vlab_api_common import get_task_logger

from vlab_deployment_api.lib import const
from vlab_deployment_api.lib.worker import vmware
from vlab_deployment_api.lib.worker import templates
from vlab_deployment_api.lib.utils import create_port_maps, delete_port_maps

app = Celery('deployment', backend='rpc://', broker=const.VLAB_MESSAGE_BROKER)


@app.task(name='deployment.show', bind=True)
def show(self, username, txn_id):
    """Obtain basic information about the deployment in a user's lab.

    :Returns: Dictionary

    :param username: The name of the user who wants info about their default gateway
    :type username: String

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_DEPLOYMENT_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        info = vmware.show_deployment(username)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    else:
        logger.info('Task complete')
        resp['content'] = info
    return resp


@app.task(name='deployment.create', bind=True)
def create(self, username, user_token, template, client_ip, txn_id):
    """Deploy a new instance of Deployment

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new deployment.
    :type username: String

    :param user_token: The JWT of a user deploying a template.
    :type user_token: String

    :param template: The name for a set of images that make up a deployment.
    :type template: String

    :param client_ip: The IP address that sent the request.
    :type client_ip: String

    :param txn_id: A unique string supplied by the client to track the call through logs.
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_DEPLOYMENT_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        resp['content'] = vmware.create_deployment(username, template, logger)
        create_port_maps(username, template, user_token, client_ip, logger)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    except RequestException as doh:
        logger.error("Not all portmap rules created. Error: %s", doh)
        resp['error'] = 'Not all portmap rules created. Error: {}'.format(doh)
    logger.info('Task complete')
    return resp


@app.task(name='deployment.delete', bind=True)
def delete(self, username, user_token, template, client_ip, txn_id):
    """Destroy a deployment.

    :Returns: Dictionary

    :param username: The name of the user who wants to delete an instance of Deployment
    :type username: String

    :param user_token: The JWT of a user destorying a deployment.
    :type user_token: String

    :param template: The name of the deployment.
    :type template: String

    :param client_ip: The IP address that sent the request.
    :type client_ip: String

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_DEPLOYMENT_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        vmware.delete_deployment(username, template, logger)
        delete_port_maps(username, template, user_token, client_ip, logger)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    except RuntimeError as doh:
        logger.error("Not all portmap rules deleted. Error: %s", doh)
        resp['error'] = 'Not all portmap rules deleted. Error: {}'.format(doh)
    else:
        logger.info('Task complete')
    return resp


@app.task(name='deployment.images', bind=True)
def images(self, verbose, txn_id):
    """Obtain a list of available deployments that can be created/deployed.

    :Returns: Dictionary

    :param verbose: Include extra details about available images/deployment templates.
    :type verbose: Boolean

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_DEPLOYMENT_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    resp['content'] = {'image': vmware.list_images(verbose=verbose)}
    logger.info('Task complete')
    return resp


@app.task(name='deployment.show_template', bind=True)
def show_template(self, username, txn_id):
    """Obtain a list of all the templates a user owns.

    :Returns: Dictionary

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_DEPLOYMENT_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        resp['content'] = templates.show(username, logger)
    except ValueError as doh:
        logger.error("Task failed")
        resp['error'] = '{}'.format(doh)
    else:
        logger.info("Task complete")
    return resp


@app.task(name='deployment.create_template', bind=True)
def create_template(self, username, template, machines, portmaps, summary, txn_id):
    """Make a new deployment template.

    :Returns: Dictionary

    :param username: The name of the account creating a deployment template.
    :type username: String

    :param template: What to name the new deployment template.
    :type template: String

    :param machines: The machines to include in the deployment template.
    :type machines: List

    :param portmaps: A mapping of machine IP to TCP port.
    :type portmaps: Dictionary

    :param summary:
    :type summary: String

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_DEPLOYMENT_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        templates.create(username, template, machines, portmaps, summary, logger)
    except ValueError as doh:
        logger.error("Task failed")
        resp['error'] = '{}'.format(doh)
    else:
        logger.info("Task complete")
    return resp


@app.task(name='deployment.delete_template', bind=True)
def delete_template(self, username, template, txn_id):
    """Destroy a deployment template that a user owns.

    :Returns: Dictionary

    :param username: The name of a user trying to delete a deployment template.
    :type username: String

    :param template: The name of the deployment template to destroy.
    :type template: String

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_DEPLOYMENT_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        templates.delete(username, template)
    except ValueError as doh:
        logger.error("Task failed")
        resp['error'] = '{}'.format(doh)
    else:
        logger.info("Task complete")
    return resp


@app.task(name='deployment.modify_template', bind=True)
def modify_template(self, username, template, summary, owner, txn_id):
    """Make minor changes to a deployment template.

    :Returns: Dictionary

    :param username: The name of the user that currently owns the template.
    :type username: String

    :param template: The name of the deployment template.
    :type template: String

    :param summary: A short description of the template.
    :type summary: String

    :param owner: The username of the new template owner.
    :type owner: String

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_DEPLOYMENT_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        templates.modify(username, template, summary, owner)
    except ValueError as doh:
        logger.error("Task failed")
        resp['error'] = '{}'.format(doh)
    else:
        logger.info("Task complete")
    return resp
