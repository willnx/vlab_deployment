# -*- coding: UTF-8 -*-
"""
A suite of tests for the functions in vmware.py
"""
import unittest
from unittest.mock import patch, MagicMock

from vlab_deployment_api.lib.worker import vmware


class TestVMware(unittest.TestCase):
    """A set of test cases for the vmware.py module"""

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_show_deployment(self, fake_vCenter, fake_consume_task, fake_get_info):
        """``deployment`` returns a dictionary when everything works as expected"""
        fake_vm = MagicMock()
        fake_vm.name = 'Deployment'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'meta': {'component': 'someDeployment',
                                               'deployment' : True,
                                               'created': 1234,
                                               'version': 'n/a',
                                               'configured': True,
                                               'generation': 1}}

        output = vmware.show_deployment(username='alice')
        expected = {'Deployment': {'meta': {'component': 'someDeployment',
                                            'deployment' : True,
                                            'created': 1234,
                                            'version': 'n/a',
                                            'configured': True,
                                            'generation': 1}}}
        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'power')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_delete_deployment(self, fake_vCenter, fake_consume_task, fake_power, fake_get_info):
        """``delete_deployment`` returns None when everything works as expected"""
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'DeploymentBox'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'meta': {'component': 'someDeployment',
                                               'deployment' : True,
                                               'created': 1234,
                                               'version': 'n/a',
                                               'configured': True,
                                               'generation': 1}}

        output = vmware.delete_deployment(username='bob', machine_name='DeploymentBox', logger=fake_logger)
        expected = None

        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'power')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_delete_deployment_value_error(self, fake_vCenter, fake_consume_task, fake_power, fake_get_info):
        """``delete_deployment`` raises ValueError when unable to find requested vm for deletion"""
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'win10'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'meta': {'component': 'someOtherComponent',
                                               'created': 1234,
                                               'version': 'n/a',
                                               'configured': True,
                                               'generation': 1}}

        with self.assertRaises(ValueError):
            vmware.delete_deployment(username='bob', machine_name='myOtherDeploymentBox', logger=fake_logger)

    @patch.object(vmware, '_check_for_deployment')
    @patch.object(vmware, 'get_meta')
    @patch.object(vmware, 'ThreadPoolExecutor')
    @patch.object(vmware, 'as_completed')
    def test_create_deployment(self, fake_as_completed, fake_ThreadPoolExecutor, fake_get_meta, fake_check_for_deployment):
        """``create_deployment`` Uses a thread pool to deploy multiple VMs at the same time."""
        username = 'louis'
        template = 'someTemplate'
        fake_check_for_deployment.return_value = ''
        logger = MagicMock()

        deployments = vmware.create_deployment(username, template, logger)

        self.assertTrue(fake_ThreadPoolExecutor.called)

    @patch.object(vmware, '_check_for_deployment')
    @patch.object(vmware, 'get_meta')
    @patch.object(vmware, 'ThreadPoolExecutor')
    @patch.object(vmware, 'as_completed')
    def test_create_deployment(self, fake_as_completed, fake_ThreadPoolExecutor, fake_get_meta, fake_check_for_deployment):
        """``create_deployment`` return info about each VM created in the deployment"""
        username = 'louis'
        template = 'someTemplate'
        logger = MagicMock()
        fake_check_for_deployment.return_value = ''
        fake_future1 = MagicMock()
        fake_future1.result.return_value = {"vm01-dply" : {"details": True}}
        fake_future2 = MagicMock()
        fake_future2.result.return_value = {"vm02-dply" : {'details' : True}}
        fake_as_completed.return_value = [fake_future1, fake_future2]
        fake_get_meta.return_value = {'machines':{
                                         'vm01':{
                                            'ova_path': '/path/to/vm01.ova',
                                            'kind' : 'SomeKindOfVM'
                                         },
                                         'vm02':{
                                            'ova_path': '/path/to/vm02.ova',
                                            'kind' : 'SomeOtherKindOfVM'
                                         },
                                       }
                                     }

        deployments = vmware.create_deployment(username, template, logger)
        expected = {'vm01-dply': {'details': True}, 'vm02-dply': {'details': True}}

        self.assertEqual(deployments, expected)

    @patch.object(vmware, '_check_for_deployment')
    @patch.object(vmware, 'get_meta')
    @patch.object(vmware, 'ThreadPoolExecutor')
    @patch.object(vmware, 'as_completed')
    def test_create_deployment_exists(self, fake_as_completed, fake_ThreadPoolExecutor, fake_get_meta, fake_check_for_deployment):
        """``create_deployment`` Raises ValueError if a deployment already exists in a user's lab."""
        username = 'louis'
        template = 'someTemplate'
        logger = MagicMock()
        fake_check_for_deployment.return_value = 'someDeployment'
        with self.assertRaises(ValueError):
            vmware.create_deployment(username, template, logger)

    @patch.object(vmware.os, 'listdir')
    def test_list_images(self, fake_listdir):
        """``list_template`` - Returns a list of available deployments that can be deployed"""
        fake_listdir.return_value = ['myDeployment']

        output = vmware.list_images()
        expected = ['myDeployment']

        # set() avoids ordering issue in test
        self.assertEqual(set(output), set(expected))

    @patch.object(vmware, 'get_meta')
    @patch.object(vmware.os, 'listdir')
    def test_list_images_verbose(self, fake_listdir, fake_get_meta):
        """``list_template`` - Returns more detail template info when passed the verbose=True argument"""
        fake_get_meta.return_value = {'info' : 'extra details'}
        fake_listdir.return_value = ['myDeployment']

        output = vmware.list_images(verbose=True)
        expected = [{'myDeployment' : {'info' : 'extra details'}}]

        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_check_for_deployment(self, fake_vCenter, fake_consume_task, fake_get_info):
        """``_check_for_deployment`` - returns an empty string when no deployments exists"""
        fake_folder = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'isi01-1'
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'meta': {'component': 'OneFS',
                                               'deployment' : False,
                                               'created': 1234,
                                               'version': 'n/a',
                                               'configured': True,
                                               'generation': 1}}
        output = vmware._check_for_deployment(username='lisa')
        expected = ''

        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_check_for_deployment_found(self, fake_vCenter, fake_consume_task, fake_get_info):
        """``_check_for_deployment`` - returns an empty string when no deployments exists"""
        fake_folder = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'isi01-1'
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'meta': {'component': 'MyAwesomeDeployment',
                                               'deployment' : True,
                                               'created': 1234,
                                               'version': 'n/a',
                                               'configured': True,
                                               'generation': 1}}
        output = vmware._check_for_deployment(username='lisa')
        expected = 'MyAwesomeDeployment'

        self.assertEqual(output, expected)

    @patch.object(vmware, 'vCenter')
    @patch.object(vmware, 'Ova')
    @patch.object(vmware, '_get_network_mapping')
    @patch.object(vmware, 'virtual_machine')
    def test_create_vm(self, fake_virtual_machine, fake_get_network_mapping, fake_Ova, fake_vCenter):
        """``_create_vm`` Returns info about the newly created VM upon success"""
        ova_file = '/path/to/some.ova'
        machine_name  = 'myNewVM'
        template = 'theTemplate'
        username = 'louis'
        vm_kind = 'InsightIQ'
        logger = MagicMock()
        the_vm = MagicMock()
        the_vm.name = machine_name
        fake_virtual_machine.deploy_from_ova.return_value = the_vm
        fake_virtual_machine.get_info.return_value = {'details': "about the vm"}

        info = vmware._create_vm(ova_file, machine_name, template, username, vm_kind, logger)
        expected = {'myNewVM': {'details': 'about the vm'}}

        self.assertEqual(info, expected)


    def test_get_network_mapping(self):
        """``_get_network_mapping`` returns the expected object when provided with not a OneFS OVA"""
        vm_kind = 'InsightIQ'
        username = 'peter'
        fake_ova = MagicMock()
        fake_ova.networks = ['foo', 'bar']
        fake_vcenter = MagicMock()
        fake_vcenter.networks = {'peter_frontend' : vmware.vim.Network('asdf')}

        net_map = vmware._get_network_mapping(fake_vcenter, fake_ova, vm_kind, username)

        self.assertTrue(isinstance(net_map, list))
        self.assertTrue(isinstance(net_map[0], vmware.vim.OvfManager.NetworkMapping))

    def test_get_network_mapping_onefs(self):
        """``_get_network_mapping`` returns the expected object when provided with a OneFS OVA"""
        vm_kind = 'OneFS'
        username = 'meg'
        fake_ova = MagicMock()
        fake_ova.networks = ['foo_frontend', 'bar_backend', 'baz_backend']
        fake_vcenter = MagicMock()
        fake_vcenter.networks = {'meg_frontend' : vmware.vim.Network('asdf'), 'meg_backend' : vmware.vim.Network('qwer')}

        net_map = vmware._get_network_mapping(fake_vcenter, fake_ova, vm_kind, username)

        self.assertTrue(isinstance(net_map, list))
        self.assertEqual(len(net_map), 3) # OneFS has 3 NICs

    def test_get_network_mapping_no_network(self):
        """``_get_network_mapping`` Raises ValueError when an expected network does not exist"""
        vm_kind = 'InsightIQ'
        username = 'peter'
        fake_ova = MagicMock()
        fake_ova.networks = ['foo', 'bar']
        fake_vcenter = MagicMock()
        fake_vcenter.networks = {}

        with self.assertRaises(ValueError):
            vmware._get_network_mapping(fake_vcenter, fake_ova, vm_kind, username)

    def test_make_onefs_network_map(self):
        """``_make_onefs_network_map`` maps all 3 of the OneFS NICs to networks in vSphere"""
        fake_vcenter = MagicMock()
        fake_vcenter.networks = {'meg_frontend' : vmware.vim.Network('asdf'), 'meg_backend' : vmware.vim.Network('qwer')}
        front_end = 'meg_frontend'
        back_end = 'meg_backend'
        ova_networks = ['some_frontend', 'some_backend', 'some_backend']

        net_map = vmware._make_onefs_network_map(ova_networks, fake_vcenter.networks, front_end, back_end)

        self.assertTrue(isinstance(net_map, list))
        self.assertEqual(len(net_map), 3)

    def test_make_onefs_network_map_no_network(self):
        """`_make_onefs_network_map`` Raises ValueError when an expected network does not exist"""
        fake_vcenter = MagicMock()
        fake_vcenter.networks = {}
        front_end = 'meg_frontend'
        back_end = 'meg_backend'
        ova_networks = ['some_frontend', 'some_backend', 'some_backend']

        with self.assertRaises(ValueError):
            vmware._make_onefs_network_map(ova_networks, fake_vcenter.networks, front_end, back_end)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'make_ova')
    @patch.object(vmware, 'vCenter')
    def test_make_ova(self, fake_vCenter, fake_make_ova, fake_get_info):
        """``_make_ova`` - Returns a tuple with the location of the new OVA upon success"""
        username = 'bart'
        machine_name = 'cowabunga'
        template_dir = '/save/ova/here'
        logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'cowabunga'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_make_ova.return_value = '/path/to/cowabunga.ova'
        fake_get_info.return_value = {'meta': {'component': 'CentOS'}}

        output = vmware._make_ova(username, machine_name, template_dir, logger)
        expected = ('/path/to/cowabunga.ova', 'CentOS', '')

        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'make_ova')
    @patch.object(vmware, 'vCenter')
    def test_make_ova_error(self, fake_vCenter, fake_make_ova, fake_get_info):
        """``_make_ova`` - Returns a tuple with an error message upon failure"""
        username = 'bart'
        machine_name = 'vm01'
        template_dir = '/save/ova/here'
        logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'cowabunga'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_make_ova.return_value = '/path/to/cowabunga.ova'

        output = vmware._make_ova(username, machine_name, template_dir, logger)
        expected = ('', '', 'No VM named vm01 found.')

        self.assertEqual(output, expected)


if __name__ == '__main__':
    unittest.main()
