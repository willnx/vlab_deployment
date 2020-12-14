# -*- coding: UTF-8 -*-
"""
A suite of tests for the functions in tasks.py
"""
import unittest
from unittest.mock import patch, MagicMock

from requests.exceptions import RequestException

from vlab_deployment_api.lib.worker import tasks


class TestTasks(unittest.TestCase):
    """A set of test cases for tasks.py"""
    @patch.object(tasks, 'vmware')
    def test_show_ok(self, fake_vmware):
        """``show`` returns a dictionary when everything works as expected"""
        fake_vmware.show_deployment.return_value = {'worked': True}

        output = tasks.show(username='bob', txn_id='myId')
        expected = {'content' : {'worked': True}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    def test_show_value_error(self, fake_vmware):
        """``show`` sets the error in the dictionary to the ValueError message"""
        fake_vmware.show_deployment.side_effect = [ValueError("testing")]

        output = tasks.show(username='bob', txn_id='myId')
        expected = {'content' : {}, 'error': 'testing', 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'create_port_maps')
    @patch.object(tasks, 'vmware')
    def test_create_ok(self, fake_vmware, fake_create_port_maps):
        """``create`` returns a dictionary when everything works as expected"""
        fake_vmware.create_deployment.return_value = {'worked': True}

        output = tasks.create(username='bob',
                              user_token='aaa.bbb.ccc',
                              template='myDeployment',
                              client_ip='1.2.3.4',
                              txn_id='myId')
        expected = {'content' : {'worked': True}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'create_port_maps')
    @patch.object(tasks, 'vmware')
    def test_create_value_error(self, fake_vmware, fake_create_port_maps):
        """``create`` sets the error in the dictionary to the ValueError message"""
        fake_vmware.create_deployment.side_effect = [ValueError("testing")]

        output = tasks.create(username='bob',
                              user_token='aaa.bbb.ccc',
                              template='myDeployment',
                              client_ip='1.2.3.4',
                              txn_id='myId')
        expected = {'content' : {}, 'error': 'testing', 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'create_port_maps')
    @patch.object(tasks, 'vmware')
    def test_create_portmap_error(self, fake_vmware, fake_create_port_maps):
        """``create`` sets the error in the dictionary when there's an issue creating all portmap rules"""
        fake_create_port_maps.side_effect = [RequestException("testing")]
        fake_vmware.create_deployment.return_value = {'things': 'stuff'}

        output = tasks.create(username='bob',
                              user_token='aaa.bbb.ccc',
                              template='myDeployment',
                              client_ip='1.2.3.4',
                              txn_id='myId')
        expected = {'content' : {'things': 'stuff'}, 'error': 'Not all portmap rules created. Error: testing', 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'delete_port_maps')
    @patch.object(tasks, 'vmware')
    def test_delete_ok(self, fake_vmware, fake_delete_port_maps):
        """``delete`` returns a dictionary when everything works as expected"""
        fake_vmware.delete_deployment.return_value = {'worked': True}

        output = tasks.delete(username='bob', user_token='aaa.bbb.ccc', template='myDeployment', client_ip='1.2.3.4', txn_id='myId')
        expected = {'content' : {}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'delete_port_maps')
    @patch.object(tasks, 'vmware')
    def test_delete_value_error(self, fake_vmware, fake_delete_port_maps):
        """``delete`` sets the error in the dictionary to the ValueError message"""
        fake_vmware.delete_deployment.side_effect = [ValueError("testing")]

        output = tasks.delete(username='bob', user_token='aaa.bbb.ccc', template='myDeployment', client_ip='1.2.3.4', txn_id='myId')
        expected = {'content' : {}, 'error': 'testing', 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'delete_port_maps')
    @patch.object(tasks, 'vmware')
    def test_delete_runtime_error(self, fake_vmware, fake_delete_port_maps):
        """``delete`` sets the error in the dictionary to the RuntimeError message"""
        fake_delete_port_maps.side_effect = [RuntimeError("testing")]

        output = tasks.delete(username='bob', user_token='aaa.bbb.ccc', template='myDeployment', client_ip='1.2.3.4', txn_id='myId')
        expected = {'content' : {}, 'error': 'Not all portmap rules deleted. Error: testing', 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    def test_images(self, fake_vmware):
        """``images`` returns a dictionary when everything works as expected"""
        fake_vmware.list_images.return_value = ['myDeployment']

        output = tasks.images(txn_id='myId', verbose=False)
        expected = {'content' : {'image' : ['myDeployment']}, 'error': None, 'params' : {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    def test_images_verbose(self, fake_vmware):
        """``images`` passes the verbose flag to the VMware lib"""
        tasks.images(txn_id='myId', verbose=True)

        the_args, the_kwargs = fake_vmware.list_images.call_args

        self.assertTrue(the_kwargs['verbose'])

    @patch.object(tasks.templates, 'show')
    def test_show_templates(self, fake_show):
        """``show_templates`` returns a dictionary when everything works as expected"""
        fake_show.return_value = ['template1', 'template2']

        output = tasks.show_template('sam', txn_id='1234')
        expected = {'content': ['template1', 'template2'], 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks.templates, 'show')
    def test_show_templates_error(self, fake_show):
        """``show_templates`` sets the error in the returned dictionary upon failure"""
        fake_show.side_effect = [ValueError("testing")]

        output = tasks.show_template('sam', txn_id='1234')
        expected = {'content': {}, 'error': "testing", 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks.templates, 'create')
    def test_create_template(self, fake_create):
        """``create_template`` - returns a dictionary when everything works as expected"""
        username = 'lisa'
        template = 'someTemplate'
        machines = ['vm01', 'vm02']
        portmaps = {'vm01' : {'target_addr': '1.2.3.4', 'port': 22}, 'vm02': {'target_addr': '1.2.3.5', 'port': 443}}
        summary = 'A cool deployment!'

        output = tasks.create_template(username, template, machines, portmaps, summary, txn_id='aabbcc')
        expected = {'content': {}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks.templates, 'create')
    def test_create_template_error(self, fake_create):
        """``create_template`` - sets the error key in the returned dictionary upon failure"""
        fake_create.side_effect = [ValueError('testing')]
        username = 'lisa'
        template = 'someTemplate'
        machines = ['vm01', 'vm02']
        portmaps = {'vm01' : {'target_addr': '1.2.3.4', 'port': 22}, 'vm02': {'target_addr': '1.2.3.5', 'port': 443}}
        summary = 'A cool deployment!'

        output = tasks.create_template(username, template, machines, portmaps, summary, txn_id='1234')
        expected = {'content': {}, 'error': "testing", 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks.templates, 'delete')
    def test_delete_template(self, fake_delete):
        """``delete_template`` returns a dictionary when everything works as expected"""
        output = tasks.delete_template(username='sam', template='someTemplate', txn_id='1234')
        expected = {'content' : {}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)


    @patch.object(tasks.templates, 'delete')
    def test_delete_templates_error(self, fake_delete):
        """``delete_template`` sets the error in the returned dictionary upon failure"""
        fake_delete.side_effect = [ValueError("testing")]

        output = tasks.delete_template(username='sam', template='someTemplate', txn_id='1234')
        expected = {'content': {}, 'error': "testing", 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks.templates, 'modify')
    def test_modify_template(self, fake_modify):
        """``modify_template`` returns a dictionary when everything works as expected"""
        output = tasks.modify_template(username='sam',
                                       template='someTemplate',
                                       summary='Cool template',
                                       owner='bob',
                                       txn_id='1234')
        expected = {'content' : {}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks.templates, 'modify')
    def test_modify_template_error(self, fake_modify):
        """``modify_template`` sets the error in the returned dictionary upon failure"""
        fake_modify.side_effect = [ValueError("testing")]
        output = tasks.modify_template(username='sam',
                                       template='someTemplate',
                                       summary='Cool template',
                                       owner='bob',
                                       txn_id='1234')
        expected = {'content' : {}, 'error': 'testing', 'params': {}}

        self.assertEqual(output, expected)


if __name__ == '__main__':
    unittest.main()
