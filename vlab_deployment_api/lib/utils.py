# -*- coding: UTF-8 -*-
"""A collection of generic utility functions"""
import ldap3
import requests

from vlab_deployment_api.lib import const
from vlab_deployment_api.lib.worker.vmware import VM_NAME_APPEND
from vlab_deployment_api.lib.template_meta_data import get_meta


def lookup_email_addr(username):
    """Query LDAP to find the email address of a user.

    :Returns: String

    :Raises ValueError:

    :param username: Who's email address is being looked up.
    """
    with open(const.AUTH_BIND_PASSWORD_LOCATION) as the_file:
        password = the_file.read().strip()
    server = ldap3.Server(const.AUTH_LDAP_URL)
    conn = ldap3.Connection(server, const.AUTH_BIND_USER, password, auto_bind=True)
    search_filter = '(&(objectclass=User)(sAMAccountName=%s))' % username
    conn.search(search_base=const.AUTH_SEARCH_BASE,
                search_filter=search_filter,
                attributes=['mail'])
    if conn.entries:
        user = conn.entries[0]
        email = user.mail.value
        conn.unbind()
    else:
        error =  'Unable to find an email address for user {}'.format(username)
        conn.unbind()
        raise ValueError(error)
    return email


def create_port_maps(username, template, user_token, client_ip, logger):
    """Add port forwarding rules to the NAT firewall of a user's lab.

    :Returns: None

    :Raises: requests.exceptions.RequestException

    :param username: The name of the vLab user.
    :type usernamne: String

    :param user_token: The JWT auth token of the user.
    :type user_token: String

    :param client_ip: The IP that issued the request.
    :type client_ip: String
    """
    url = 'https://{}.{}/api/1/ipam/portmap'.format(username, const.VLAB_FQDN)
    headers = {'X-Auth' : user_token, 'X-Forwarded-For': client_ip}
    portmaps = get_meta(template)['machines']
    for vm_name, info in portmaps.items():
        for tcp_port in info['ports']:
            payload = {'target_addr': info['ip'],
                       'target_port': tcp_port,
                       'target_name': '{}{}'.format(vm_name, VM_NAME_APPEND),
                       'target_component': template,
                      }
            resp = requests.post(url, json=payload, headers=headers, verify=False) # user gateways have a self-signed cert
            resp.raise_for_status()


def delete_port_maps(username, template, user_token, client_ip, logger):
    """Delete the port forwarding rules to the VMs of a deployment in a user's lab.

    :Returns: None

    :Raises: RuntimeError

    :param username: The name of the vLab user.
    :type usernamne: String

    :param user_token: The JWT auth token of the user.
    :type user_token: String

    :param client_ip: The IP that issued the request.
    :type client_ip: String
    """
    url = 'https://{}.{}/api/1/ipam/portmap'.format(username, const.VLAB_FQDN)
    headers = {'X-Auth' : user_token, 'X-Forwarded-For': client_ip}
    all_ports = requests.get(url, params={'component': template}, headers=headers, verify=False).json()['content']['ports']
    errors = []
    for port in all_ports.keys():
        resp = requests.delete(url, json={'conn_port': int(port)}, headers=headers, verify=False)
        if not resp.ok:
            errors.append(resp.content.decode(errors='replace'))
    if errors:
        msg = '\n'.join(errors)
        raise RuntimeError(msg)
