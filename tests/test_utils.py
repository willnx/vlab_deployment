# -*- coding: UTF-8 -*-
"""A suite of unit tests for the utils.py module"""
import unittest
from unittest.mock import patch, MagicMock

from vlab_deployment_api.lib import utils


class TestUtils(unittest.TestCase):
    """A set of test cases for the ``utils.py`` module"""

    @patch.object(utils.ldap3, 'Connection')
    @patch.object(utils, 'open')
    def test_lookup_email_addr(self, fake_open, fake_Connection):
        """``utils`` - lookup_email_addr returns an email address"""
        fake_open.return_value.__enter__.return_value.read.return_value = 'the_password'
        fake_entry = MagicMock()
        fake_entry.mail.value = 'sam@vlab.org'
        fake_Connection.return_value.entries = [fake_entry]

        output = utils.lookup_email_addr('sam')
        expected = 'sam@vlab.org'

        self.assertEqual(output, expected)

    @patch.object(utils.ldap3, 'Connection')
    @patch.object(utils, 'open')
    def test_lookup_email_addr_unbinds(self, fake_open, fake_Connection):
        """``utils`` - lookup_email_addr closes the TCP connection to the LDAP server upon success."""
        fake_open.return_value.__enter__.return_value.read.return_value = 'the_password'
        fake_entry = MagicMock()
        fake_entry.mail.value = 'sam@vlab.org'
        fake_Connection.return_value.entries = [fake_entry]

        utils.lookup_email_addr('sam')

        self.assertTrue(fake_Connection.return_value.unbind.called)

    @patch.object(utils.ldap3, 'Connection')
    @patch.object(utils, 'open')
    def test_lookup_email_addr_error(self, fake_open, fake_Connection):
        """``utils`` - lookup_email_addr raises ValueError when no email is found"""
        fake_open.return_value.__enter__.return_value.read.return_value = 'the_password'
        fake_entry = MagicMock()
        fake_Connection.return_value.entries = []

        with self.assertRaises(ValueError):
            utils.lookup_email_addr('sam')

    @patch.object(utils.ldap3, 'Connection')
    @patch.object(utils, 'open')
    def test_lookup_email_addr_error_unbinds(self, fake_open, fake_Connection):
        """``utils`` - lookup_email_addr closes the TCP connection to the LDAP server upon failure"""
        fake_open.return_value.__enter__.return_value.read.return_value = 'the_password'
        fake_entry = MagicMock()
        fake_Connection.return_value.entries = []

        try:
            utils.lookup_email_addr('sam')
        except ValueError:
            pass

        self.assertTrue(fake_Connection.return_value.unbind.called)

    @patch.object(utils, 'get_meta')
    @patch.object(utils.requests, 'post')
    def test_create_port_maps(self, fake_post, fake_get_meta):
        """``utils`` - create_port_maps constructs the correct URL"""
        username = 'homer'
        template = 'doh'
        user_token = 'aaa.bbb.ccc'
        client_ip = '1.2.3.4'
        logger = MagicMock()
        fake_get_meta.return_value = {'machines': {'vm01' : {'ip': '3.3.3.3', 'kind': 'Donut', 'ports':[22, 443]}}}
        utils.create_port_maps(username, template, user_token, client_ip, logger)

        the_args, _ = fake_post.call_args
        expected = ('https://homer.vlab.local/api/1/ipam/portmap',)

        self.assertEqual(the_args, expected)

    @patch.object(utils, 'get_meta')
    @patch.object(utils.requests, 'post')
    def test_create_port_maps_raises(self, fake_post, fake_get_meta):
        """``utils`` - create_port_maps raises an exception if the HTTP request fails"""
        username = 'homer'
        template = 'doh'
        user_token = 'aaa.bbb.ccc'
        client_ip = '1.2.3.4'
        logger = MagicMock()
        fake_get_meta.return_value = {'machines': {'vm01' : {'ip': '3.3.3.3', 'kind': 'Donut', 'ports':[22, 443]}}}
        utils.create_port_maps(username, template, user_token, client_ip, logger)

        self.assertTrue(fake_post.return_value.raise_for_status.called)

    @patch.object(utils.requests, 'delete')
    @patch.object(utils.requests, 'get')
    def test_delete_port_maps(self, fake_get, fake_delete):
        """``utils`` - delete_port_maps looks up existing port forwarding rules"""
        username = 'homer'
        template = 'doh'
        user_token = 'aaa.bbb.ccc'
        client_ip = '1.2.3.4'
        logger = MagicMock()
        fake_get.return_value.json.return_value = {'content': {'ports': {'50024': {'name': 'foo', 'target_addr': '1.2.3.4', 'target_port' : '443',  'component': 'myTemplate'}}}}

        utils.delete_port_maps(username, template, user_token, client_ip, logger)

        self.assertTrue(fake_get.called)

    @patch.object(utils.requests, 'delete')
    @patch.object(utils.requests, 'get')
    def test_delete_port_maps_error(self, fake_get, fake_delete):
        """``utils`` - delete_port_maps Raises RuntimeError is deleting a rule fails"""
        username = 'homer'
        template = 'doh'
        user_token = 'aaa.bbb.ccc'
        client_ip = '1.2.3.4'
        logger = MagicMock()
        fake_get.return_value.json.return_value = {'content': {'ports': {'50024': {'name': 'foo', 'target_addr': '1.2.3.4', 'target_port' : '443',  'component': 'myTemplate'}}}}
        fake_resp = MagicMock()
        fake_resp.ok = False
        fake_resp.content = b'someError'
        fake_delete.return_value = fake_resp

        with self.assertRaises(RuntimeError):
            utils.delete_port_maps(username, template, user_token, client_ip, logger)




if __name__ == '__main__':
    unittest.main()
