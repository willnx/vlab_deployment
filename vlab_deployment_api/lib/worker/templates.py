# -*- coding: UTF-8 -*-
"""A module for interacting with deployment templates"""
import os
import glob
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

from vlab_deployment_api.lib import const
from vlab_deployment_api.lib.worker import vmware
from vlab_deployment_api.lib.utils import lookup_email_addr
from vlab_deployment_api.lib.template_meta_data import get_meta, set_meta, update_meta, map_machine


def show(username, logger):
    """Lookup templates that a user owns

    :Returns: Dictionary

    :param username: The name of the user lookup up templates they own.
    :type username: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    templates = {}
    for template in os.listdir(const.VLAB_DEPLOYMENT_TEMPLATE_DIR):
        meta = get_meta(template)
        if meta['owner'] == username:
            templates[template] = meta
    return templates


def create(username, template, machines, portmaps, summary, logger):
    """Make a new deployment template.

    :Returns: None

    :Raises: ValueError

    :param username: The user creating a new deployment template.
    :type username: String

    :param template: What to name the new deployment template.
    :type template: String

    :param machines: The machines to include in the deployment template.
    :type machines: List

    :param portmaps: A mapping of machine IP to TCP port.
    :type portmaps: Dictionary

    :param summary: A short description of the deployment template.
    :type summary: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    hidden_template_dir = os.path.join(const.VLAB_DEPLOYMENT_TEMPLATE_DIR, '.{}'.format(template))
    try:
        check_for_template(template)
        os.makedirs(hidden_template_dir)
    except FileExistsError:
        raise ValueError('A template named {} already exists. Try a new/different name.'.format(template))
    futures = set()
    failures = []
    vm_kind_map = {}
    with ThreadPoolExecutor(max_workers=const.VLAB_DEPLOY_CONCURRENT_VMS) as executor:
        for machine_name in machines:
            future = executor.submit(vmware._make_ova, username, machine_name, hidden_template_dir, logger)
            futures.add(future)
        for future in as_completed(futures):
            try:
                new_ova, kind, error = future.result()
            except Exception as doh:
                logger.exception(doh)
                failures.append(str(doh))
            else:
                name = os.path.splitext(os.path.basename(new_ova))[0]
                vm_kind_map[name] = kind
    if failures:
        shutil.rmtree(hidden_template_dir)
        error_message = 'Failed to create template. Error(s): {}'.format(' '.join(failures))
        raise ValueError(error_message)
    else:
        machine_meta = create_machine_meta(template, portmaps, vm_kind_map)
        email = lookup_email_addr(username)
        set_meta(template, username, email, summary, machine_meta)
        template_dir = os.path.join(const.VLAB_DEPLOYMENT_TEMPLATE_DIR, template)
        # Hidden directories is how we avoid someone trying to deploy a template
        # while it's still being created.
        os.rename(hidden_template_dir, template_dir)


def delete(username, template):
    """Destroy a deployment template. Raises a ValueError if the user does not own
    the template.

    :Returns: None

    :Raises: ValueError

    :param username: The name of a user trying to delete a deployment template.
    :type username: String

    :param template: The name of the deployment template to destroy.
    :type template: String
    """
    error = ''
    for a_template in os.listdir(const.VLAB_DEPLOYMENT_TEMPLATE_DIR):
        if template == a_template:
            meta = get_meta(template)
            if meta['owner'] == username:
                template_path = os.path.join(const.VLAB_DEPLOYMENT_TEMPLATE_DIR, template)
                shutil.rmtree(template_path)
            else:
                error = 'Unable to delete templates you do not own. {} is owned by {}'.format(template, meta['owner'])
    if error:
        raise ValueError(error)


def modify(username, template, summary, owner, email=None):
    """Update some of the meta data of a deployment template.

    :Returns: None

    :param username: The current owner of a the deployment template.
    :type username: String

    :param template: The deployment template to modify.
    :type template: String

    :param summary: The new description for a deployment template.
    :type summary: String

    :param owner: The new owner of a deployment template.
    :type owner: String

    :param email: The new email of the deployment template owner.
    :type email: String
    """
    if owner:
        email = lookup_email_addr(owner)
    update_meta(template,
                username=username,
                owner=owner,
                email=email,
                summary=summary)


def check_for_template(template):
    """Ensures a template with the same name doesn't already exist.

    :Raises: FileExistsError

    :param template: The name for a deployment template
    :type template: String
    """
    template_dir = os.path.join(const.VLAB_DEPLOYMENT_TEMPLATE_DIR, template)
    if os.path.isdir(template_dir):
        raise FileExistsError()


def create_machine_meta(template, portmaps, vm_kind_map):
    """
    :Returns: Dictionary

    :param template: The name of the deployment template.
    :type template: String

    :param portmaps: A mapping of machine name to IP & TCP port values for portmap rules.
    :type portmaps: Dictionary
    """
    machines_meta = {}
    for machine in portmaps:
        kind = vm_kind_map[machine['name']]
        meta = map_machine(name=machine['name'].replace(vmware.VM_NAME_APPEND, ''),
                           ip=machine['target_addr'],
                           ports=machine['target_ports'],
                           kind=kind)
        machines_meta.update(meta)
    return machines_meta
