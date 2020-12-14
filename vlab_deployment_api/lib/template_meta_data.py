# -*- coding: UTF-8 -*-
"""This module handles reading/writing/updating the meta data for a deployment template"""
import os

import ujson

from vlab_deployment_api.lib import const

META_FILE_NAME = 'meta.json'

"""
{"owner": <username>,
 "email": <email of owner>,
 "summary": <A short description that provides context about the template>,
 "machines": {
    <name of VM>: {
        "ip": <the primary IP - used to make portmap rules in NAT firewall>,
        "kind": <the type of VM; i.e. OneFS, InsightIQ, etc>,
        "ova_path": <The file system location of the OVA for this VM>,
        "ports": [<the TCP ports of the VM's control path>]
    }
 }
}
"""

def get_meta(template):
    """Public function to obtain meta-data about a deployment template.

    :Returns: String

    :param template: The name of the deployment template
    :type template: String
    """
    meta = _read_meta(template)
    template_dir = os.path.dirname(_get_template_path(template))
    # dynamically add the 'ova_path' attribute
    # This avoids a "cache invalidation is hard" problem when the ``const.VLAB_DEPLOYMENT_TEMPLATE_DIR``
    # value changes in the future.
    for dir_item in os.listdir(template_dir):
        if not dir_item.endswith('.ova'):
            continue
        machine_name = dir_item.replace('.ova', '')
        ova_path = os.path.join(template_dir, dir_item)
        meta['machines'][machine_name]['ova_path'] = ova_path
    return meta


def set_meta(template, owner, email, summary, machines):
    """Only should be used when first creating a deployment template.

    :Returns: None

    :param template: The name of the deployment template.
    :type template: String

    :param owner: The user that the deployment template belongs to.
    :type owner: String

    :param email: The email address of the owner.
    :type email: String

    :param summary: A short description that provides context about the deployment template.
    :type summary: String
    """
    meta = {'owner': owner, 'email': email, 'summary': summary, 'machines': machines}
    _write_meta(template, meta, hidden=True)


def update_meta(template, username='', owner=None, summary=None, email=None):
    """Public function to make small/minor changes to the deployment template meta data.

    :Returns: None

    :Raises: ValueError

    :param template: The deployment template to modify.
    :type template: String

    :param username: The new owner of a the deployment template.
    :type username: String

    :param owner: The current owner of a deployment template.
    :type owner: String

    :param summary: The new description for a deployment template.
    :type summary: String

    :param email: The new email of the deployment template owner.
    :type email: String
    """
    meta = _read_meta(template)
    if meta['owner'] == username:
        new_meta = {'owner': owner, 'email': email, 'summary': summary}
        new_meta = {x:y for x,y in new_meta.items() if y is not None}
        meta.update(new_meta)
        _write_meta(template, meta)
    else:
        error = 'Unable to update templates you do not own. {} currently owned by {}'.format(template, meta['owner'])
        raise ValueError(error)


def map_machine(name, ip, kind, ports):
    """Constructs the "machines" part of the meta data.

    For template with multiple machines, call this function for each machine
    then combine/union the returned dictionaries.

    :param name: The name of the machine.
    :type name: String

    :param kind: The type of machine.
    :type kind: String

    :param ip: The primary IP address of the machine. Used when making port map rules.
    :type ip: String

    :param ports: The TCP port numbers of the machine's control plane.
    :type ports: List
    """
    machine = {name: {"ip": ip, "kind": kind, "ports": ports}}
    return machine


def _write_meta(template, meta, hidden=False):
    """Makes the code DRYer - Overwrites existing content.

    :Returns: None

    :param template: The name of the deployment template
    :type template: String

    :param meta: The contents to write to the meta data file.
    :type meta: Dictionary
    """
    template_path = _get_template_path(template, hidden=hidden)
    with open(template_path, 'w') as the_file:
        ujson.dump(meta, the_file)


def _read_meta(template):
    """Makes the code DRYer

    :Returns: String

    :param template: The name of the deployment template
    :type template: String
    """
    template_path = _get_template_path(template)
    with open(template_path) as the_file:
        meta = ujson.load(the_file)
    return meta


def _get_template_path(template, hidden=False):
    """Makes the code DRYer

    :Returns: String

    :param template: The name of the deployment template
    :type template: String

    :param hidden: Set to True when editing meta data for a template that's currently being created.
    :type hidden: Boolean
    """
    if hidden:
        template_dir = os.path.join(const.VLAB_DEPLOYMENT_TEMPLATE_DIR, '.{}'.format(template))
    else:
        template_dir = os.path.join(const.VLAB_DEPLOYMENT_TEMPLATE_DIR, template)
    return os.path.join(template_dir, META_FILE_NAME)
