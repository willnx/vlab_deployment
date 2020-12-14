# -*- coding: UTF-8 -*-
"""A suite of unit tests for the ``templates.py`` module"""
import unittest
from unittest.mock import patch, MagicMock

from vlab_deployment_api.lib.worker import templates


class TestShow(unittest.TestCase):
    """A set of test cases for the ``show`` function"""

    @patch.object(templates.os, 'listdir')
    @patch.object(templates, 'get_meta')
    def test_show(self, fake_get_meta, fake_listdir):
        """``templates`` - show returns a dictionary of meta-data for templates a user owns"""
        fake_listdir.return_value = ['foo']
        fake_get_meta.return_value = {'owner': "jill"}
        logger = MagicMock()
        output = templates.show('jill', logger)
        expected = {'foo': {'owner': "jill"}}

        self.assertEqual(output, expected)

    @patch.object(templates.os, 'listdir')
    @patch.object(templates, 'get_meta')
    def test_show_none(self, fake_get_meta, fake_listdir):
        """``templates`` - show returns an empty dictionary if a user owns no templates"""
        fake_listdir.return_value = ['foo']
        fake_get_meta.return_value = {'owner': "jill"}
        logger = MagicMock()
        output = templates.show('bob', logger)
        expected = {}

        self.assertEqual(output, expected)


class TestCreate(unittest.TestCase):
    """A set of test cases for the ``create`` function"""

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.username = 'lisa'
        cls.template = 'someTemplate'
        cls.machines = ['vm01', 'vm02']
        cls.portmaps = [{'name': 'vm01', 'target_addr': '1.2.3.4', 'target_port': 22}, {'name' : 'vm02', 'target_addr': '1.2.3.5', 'target_port': 443}]
        cls.summary = 'My cool deployment template!'
        cls.logger = MagicMock()

    @patch.object(templates, 'set_meta')
    @patch.object(templates, 'as_completed')
    @patch.object(templates, 'check_for_template')
    @patch.object(templates.os, 'makedirs')
    @patch.object(templates.vmware, '_make_ova')
    @patch.object(templates.shutil, 'rmtree')
    @patch.object(templates, 'create_machine_meta')
    @patch.object(templates, 'lookup_email_addr')
    @patch.object(templates.os, 'rename')
    def test_create(self, fake_rename, fake_lookup_email_addr, fake_create_machine_meta,
        fake_rmtree, fake_make_ova, fake_makedirs, fake_check_for_template, fake_as_completed,
        fake_set_meta):
        """``templates`` - create returns None"""
        output = templates.create(self.username,
                                  self.template,
                                  self.machines,
                                  self.portmaps,
                                  self.summary,
                                  self.logger)

        self.assertTrue(output is None)

    @patch.object(templates, 'set_meta')
    @patch.object(templates, 'as_completed')
    @patch.object(templates, 'check_for_template')
    @patch.object(templates.os, 'makedirs')
    @patch.object(templates.vmware, '_make_ova')
    @patch.object(templates.shutil, 'rmtree')
    @patch.object(templates, 'create_machine_meta')
    @patch.object(templates, 'lookup_email_addr')
    @patch.object(templates.os, 'rename')
    def test_create_rename(self, fake_rename, fake_lookup_email_addr, fake_create_machine_meta,
        fake_rmtree, fake_make_ova, fake_makedirs, fake_check_for_template, fake_as_completed,
        fake_set_meta):
        """``templates`` - create makes the template directory unhidden when successful"""
        templates.create(self.username,
                         self.template,
                         self.machines,
                         self.portmaps,
                         self.summary,
                         self.logger)

        the_args, _ = fake_rename.call_args
        expected = ('/templates/.someTemplate', '/templates/someTemplate')

        self.assertEqual(the_args, expected)

    @patch.object(templates, 'set_meta')
    @patch.object(templates, 'as_completed')
    @patch.object(templates, 'check_for_template')
    @patch.object(templates.os, 'makedirs')
    @patch.object(templates.vmware, '_make_ova')
    @patch.object(templates.shutil, 'rmtree')
    @patch.object(templates, 'create_machine_meta')
    @patch.object(templates, 'lookup_email_addr')
    @patch.object(templates.os, 'rename')
    def test_create_template_exists(self, fake_rename, fake_lookup_email_addr, fake_create_machine_meta,
        fake_rmtree, fake_make_ova, fake_makedirs, fake_check_for_template, fake_as_completed,
        fake_set_meta):
        """``templates`` - create raises ValueError if the template already exists"""
        fake_check_for_template.side_effect = [FileExistsError('testing')]
        with self.assertRaises(ValueError):
            output = templates.create(self.username,
                                      self.template,
                                      self.machines,
                                      self.portmaps,
                                      self.summary,
                                      self.logger)

    @patch.object(templates, 'set_meta')
    @patch.object(templates, 'as_completed')
    @patch.object(templates, 'check_for_template')
    @patch.object(templates.os, 'makedirs')
    @patch.object(templates.vmware, '_make_ova')
    @patch.object(templates.shutil, 'rmtree')
    @patch.object(templates, 'create_machine_meta')
    @patch.object(templates, 'lookup_email_addr')
    @patch.object(templates.os, 'rename')
    def test_create_template_exception(self, fake_rename, fake_lookup_email_addr, fake_create_machine_meta,
        fake_rmtree, fake_make_ova, fake_makedirs, fake_check_for_template, fake_as_completed,
        fake_set_meta):
        """``templates`` - create raises ValueError if template creation raises an exception"""
        fake_future = MagicMock()
        fake_future.result.side_effect = RuntimeError('testing')
        fake_as_completed.return_value = [fake_future]

        with self.assertRaises(ValueError):
            output = templates.create(self.username,
                                      self.template,
                                      self.machines,
                                      self.portmaps,
                                      self.summary,
                                      self.logger)

    @patch.object(templates, 'set_meta')
    @patch.object(templates, 'as_completed')
    @patch.object(templates, 'check_for_template')
    @patch.object(templates.os, 'makedirs')
    @patch.object(templates.vmware, '_make_ova')
    @patch.object(templates.shutil, 'rmtree')
    @patch.object(templates, 'create_machine_meta')
    @patch.object(templates, 'lookup_email_addr')
    @patch.object(templates.os, 'rename')
    def test_create_template_error(self, fake_rename, fake_lookup_email_addr, fake_create_machine_meta,
        fake_rmtree, fake_make_ova, fake_makedirs, fake_check_for_template, fake_as_completed,
        fake_set_meta):
        """``templates`` - create raises ValueError if unable to create the template"""
        fake_future = MagicMock()
        fake_future.result.return_value = [('', 'some error')]
        fake_as_completed.return_value = [fake_future]

        with self.assertRaises(ValueError):
            output = templates.create(self.username,
                                      self.template,
                                      self.machines,
                                      self.portmaps,
                                      self.summary,
                                      self.logger)

    @patch.object(templates, 'set_meta')
    @patch.object(templates, 'as_completed')
    @patch.object(templates, 'check_for_template')
    @patch.object(templates.os, 'makedirs')
    @patch.object(templates.vmware, '_make_ova')
    @patch.object(templates.shutil, 'rmtree')
    @patch.object(templates, 'create_machine_meta')
    @patch.object(templates, 'lookup_email_addr')
    @patch.object(templates.os, 'rename')
    def test_create_template_fails_cleanup(self, fake_rename, fake_lookup_email_addr, fake_create_machine_meta,
        fake_rmtree, fake_make_ova, fake_makedirs, fake_check_for_template, fake_as_completed,
        fake_set_meta):
        """``templates`` - create deletes the partial template when unable to create the whole template"""
        fake_future = MagicMock()
        fake_future.result.side_effect = RuntimeError('testing')
        fake_as_completed.return_value = [fake_future]

        try:
            output = templates.create(self.username,
                                      self.template,
                                      self.machines,
                                      self.portmaps,
                                      self.summary,
                                      self.logger)
        except ValueError:
            pass

        self.assertTrue(fake_rmtree.called)


class TestDelete(unittest.TestCase):
    """A set of test cases for the ``delete`` function"""

    @patch.object(templates.shutil, 'rmtree')
    @patch.object(templates.os, 'listdir')
    @patch.object(templates, 'get_meta')
    def test_delete(self, fake_get_meta, fake_listdir, fake_rmtree):
        """``templates`` delete returns None upon success"""
        fake_listdir.return_value = ['someTemplate']
        fake_get_meta.return_value = {'owner': "jill"}

        output = templates.delete('jill', 'someTemplate')
        expected = None

        self.assertEqual(output, expected)

    @patch.object(templates.shutil, 'rmtree')
    @patch.object(templates.os, 'listdir')
    @patch.object(templates, 'get_meta')
    def test_delete_error(self, fake_get_meta, fake_listdir, fake_rmtree):
        """``templates`` delete raises ValueError if a user tries to delete a template they do not own."""
        fake_listdir.return_value = ['someTemplate']
        fake_get_meta.return_value = {'owner': "jill"}

        with self.assertRaises(ValueError):
            templates.delete('bob', 'someTemplate')


class TestModify(unittest.TestCase):
    """A set of test cases for the ``modify`` function"""

    @patch.object(templates, 'lookup_email_addr')
    @patch.object(templates, 'update_meta')
    def test_modify(self, fake_update_meta, fake_lookup_email_addr):
        """``templates`` modify looks up the new owner's email"""
        templates.modify('someTemplate', 'newOwner', 'oldOlder', 'What a cool template')

        self.assertTrue(fake_lookup_email_addr.called)


class TestFunctions(unittest.TestCase):
    """A suite of test cases for the miscellaneous functions in the ``templates.py`` module"""

    @patch.object(templates.os.path, 'isdir')
    def test_check_for_template(self, fake_isdir):
        """``templates`` check_for_template raises FileExistsError if the template already exists"""
        fake_isdir.return_value = True

        with self.assertRaises(FileExistsError):
            templates.check_for_template('foo')

    def test_create_machine_meta(self):
        """``templates`` create_machine_meta constructs the expected dictionary"""
        portmaps = [{'name': 'vm01', 'target_addr': '1.2.3.4', 'target_ports': [22]}, {'name' : 'vm02', 'target_addr': '1.2.3.5', 'target_ports': [443]}]
        template = 'myCoolTemplate'

        output = templates.create_machine_meta(template, portmaps)
        expected = {'vm01': {'ip': '1.2.3.4', 'kind': 'myCoolTemplate', 'ports': [22]},
                    'vm02': {'ip': '1.2.3.5', 'kind': 'myCoolTemplate', 'ports': [443]}}

        self.assertEqual(output, expected)


if __name__ == '__main__':
    unittest.main()
