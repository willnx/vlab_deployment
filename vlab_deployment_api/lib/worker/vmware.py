# -*- coding: UTF-8 -*-
"""Business logic for backend worker tasks"""
import time
import glob
import random
import os.path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import ujson
from vlab_inf_common.vmware import vCenter, Ova, vim, virtual_machine, consume_task

from vlab_deployment_api.lib import const
from vlab_deployment_api.lib.template_meta_data import get_meta

VM_NAME_APPEND = '-dply'


def show_deployment(username):
    """Obtain basic information about Deployment

    :Returns: Dictionary

    :param username: The user requesting info about their Deployment
    :type username: String
    """
    info = {}
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        deployment_vms = {}
        for vm in folder.childEntity:
            info = virtual_machine.get_info(vcenter, vm, username)
            if info['meta'].get('deployment', False) == True:
                deployment_vms[vm.name] = info
    return deployment_vms


def delete_deployment(username, machine_name, logger):
    """Unregister and destroy a user's Deployment

    :Returns: None

    :param username: The user who wants to delete their jumpbox
    :type username: String

    :param machine_name: The name of the VM to delete
    :type machine_name: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        tasks = []
        for entity in folder.childEntity:
            info = virtual_machine.get_info(vcenter, entity, username)
            if info['meta'].get('deployment', False) == True:
                logger.debug('powering off VM %s', entity.name)
                virtual_machine.power(entity, state='off')
                delete_task = entity.Destroy_Task()
                tasks.append(delete_task)
        if tasks:
            logger.debug('blocking while VMs are being destroyed')
            for task in tasks:
                consume_task(task)

        else:
            raise ValueError('No {} named {} found'.format('deployment', machine_name))


def create_deployment(username, template, logger):
    """Deploy a new instance of Deployment

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new Deployment
    :type username: String

    :param template: The name of template being deployed.
    :type template: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    current_deployment = _check_for_deployment(username)
    if current_deployment:
        error = "Multiple deployments per lab not allowed. Current have deployed: {}".format(current_deployment)
        raise ValueError(error)
    logger.info("Deploying template: %s", template)
    meta = get_meta(template)
    deployments = {}
    futures = set()
    with ThreadPoolExecutor(max_workers=const.VLAB_DEPLOY_CONCURRENT_VMS) as executor:
        for machine_name, details in meta['machines'].items():
            # Avoids deploy failure due to the user have a VM by the same name
            # as a VM in a deployment template.
            deploy_name = '{}{}'.format(machine_name, VM_NAME_APPEND)
            future = executor.submit(_create_vm, details['ova_path'], deploy_name, template, username, details['kind'], logger)
            futures.add(future)
        for future in as_completed(futures):
            deployments.update(future.result())
    return deployments


def list_images(verbose=False):
    """Obtain a list of available versions of Deployment that can be created

    :Returns: List

    :param verbose: Include details about each deployment template.
    :type verbose: Boolean
    """
    answer = []
    images = [x for x in os.listdir(const.VLAB_DEPLOYMENT_TEMPLATE_DIR) if not x.startswith('.')]
    if verbose:
        # This exists so the API can return handy info. The deployments service
        # is unique, in that the templates are created and managed by users.
        # The other services (like OneFS, InsightIQ, etc) are all managed by the
        # sysadmin. So returning a simple list of what's available works for those
        # services. The default of "False" is so we automatically mimic the behavior
        # of those services when the RESTful API gets called; just give them a
        # simple list of what's available. As an API client/consumer, I always get
        # annoyed when two similar API end points return different data structures...
        for template in images:
            meta = get_meta(template)
            detailed_info = {template: meta}
            answer.append(detailed_info)
    else:
        answer = images
    return answer


def _check_for_deployment(username):
    """For many reasons, only 1 deployment per lab is allowed. This function
    checks if a deployment already exists.

    :Returns: String

    :param username: The name of the user who wants to create a new Deployment
    :type username: String
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER,
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        current_deployment = ''
        for vm in folder.childEntity:
            info = virtual_machine.get_info(vcenter, vm, username)
            if info['meta'].get('deployment', False):
                current_deployment = info['meta']['component']
                break
    return current_deployment


def _create_vm(ova_file, machine_name, template, username, vm_kind, logger):
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER,
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        ova = Ova(ova_file)
        try:
            net_map = _get_network_mapping(vcenter, ova, vm_kind, username)
            the_vm = virtual_machine.deploy_from_ova(vcenter=vcenter,
                                                     ova=ova,
                                                     network_map=net_map,
                                                     username=username,
                                                     machine_name=machine_name,
                                                     logger=logger)
        finally:
            ova.close()

        meta_data = {'component' : template,
                     'created' : time.time(),
                     'deployment': True,
                     'version' : 'n/a',
                     'configured' : True,
                     'generation' : 1}
        virtual_machine.set_meta(the_vm, meta_data)
        info = virtual_machine.get_info(vcenter, the_vm, username, ensure_ip=False)
        return {the_vm.name: info}


def _get_network_mapping(vcenter, ova, vm_kind, username):
    """Obtain an object that maps the VMs NIC(s) to virtual networks in vSphere.

    :Returns: List

    :param vcenter: The vCenter object
    :type vcenter: vlab_inf_common.vmware.vcenter.vCenter

    :param ova: The Ova object
    :type ova: vlab_inf_common.vmware.ova.Ova

    :param vm_kind: The type of component to create a network map for. (i.e. OneFS, InsightIQ, ECS, etc)
    :type vm_kind: String

    :param username: The name of the user deploying VMs.
    :type username: String
    """
    front_end = '{}_frontend'.format(username)
    back_end = '{}_backend'.format(username)
    if vm_kind.lower() == 'onefs':
        net_map = _make_onefs_network_map(vcenter.networks, front_end, back_end)
    else:
        try:
            net_map = vim.OvfManager.NetworkMapping()
            net_map.name = ova.networks[0]
            net_map.network = vcenter.networks[front_end]
            net_map = [net_map] # the vCenter API wants a list...
        except KeyError:
            raise ValueError('No such network named {}'.format(front_end))
    return net_map


def _make_onefs_network_map(vcenter_networks, front_end, back_end):
    """The OneFS VMs have 3 NICs. This function maps the correct frontend/backend
    NICs to the appropriate networks in vSphere.

    :Returns: List

    :param vcenter_networks: All the networks in vSphere.
    :type vcenter_networks: Dictionary

    :param front_end: The public network clients use to connect to OneFS.
    :type front_end: String

    :parm back_end: The private/internal network used by OneFS.
    :type back_end: String
    """
    net_map = []
    mapping = [('hostonly', back_end),
               ('nat', front_end),
               ('bridged', back_end)]
    for ova_network, vlab_network in mapping:
        map = vim.OvfManager.NetworkMapping()
        map.name = ova_network
        try:
            map.network = vcenter_networks[vlab_network]
        except KeyError:
            error = 'No network named {}'.format(vlab_network)
            raise ValueError(error)
        net_map.append(map)
    return net_map


def _make_ova(username, machine_name, template_dir, logger):
    """Export a VM to an OVA.

    :param username: The user creating a new deployment template.
    :type username: String

    :param machine_name: The name of the VM to include in the deployment template.
    :type machine_name: String

    :param template_dir: The folder to save the new VM OVA in.
    :type template_dir: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    new_ova = ''
    error = ''
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER,
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for vm in folder.childEntity:
            if vm.name == machine_name:
                # Avoids VM names getting crazy long as a result of users making
                # new templates from existing deployments.
                ova_name = vm.name.replace(VM_NAME_APPEND, '')
                new_ova = virtual_machine.make_ova(vcenter, vm, template_dir, logger, ova_name=ova_name)
                break
        else:
            error = 'No VM named {} found.'.format(machine_name)
    return new_ova, error
