# -*- coding: UTF-8 -*-
"""
A suite of tests for the functions in template_meta_data.py module
"""
import os
import unittest
from unittest.mock import patch, MagicMock

from vlab_deployment_api.lib import template_meta_data


class TestGetMeta(unittest.TestCase):
    """A set of test cases for the ``get_meta`` function"""

    @patch.object(template_meta_data.os, 'listdir')
    @patch.object(template_meta_data, '_read_meta')
    def test_get_meta(self, fake_read_meta, fake_listdir):
        """``_get_meta`` Dynamically adds the ova_path property to the meta data returned"""
        fake_listdir.return_value = ['someVM.ova', 'aFile.json']
        fake_read_meta.return_value = {"machines": {"someVM": {"ip": "1.2.3.4", "kind": "foo"}}}

        meta = template_meta_data.get_meta(template='foo')
        expected = {'machines': {'someVM': {'ip': '1.2.3.4', 'kind': 'foo', 'ova_path': '/templates/foo/someVM.ova'}}}

        self.assertEqual(meta, expected)


class TestSetMeta(unittest.TestCase):
    """A set of test cases for the ``set_meta`` function"""

    @patch.object(template_meta_data, '_write_meta')
    def test_set_meta(self, fake_write_meta):
        """``template_meta_data`` - The set_meta writes out the expected content"""
        template = 'the best template ever'
        owner = 'bob'
        email = 'bob@vlab.org'
        summary = "Look at this cool template I made!"
        machines = {'vm01': "some info"}

        template_meta_data.set_meta(template, owner, email, summary, machines)

        the_args, _ = fake_write_meta.call_args
        expected = (template, {'email': 'bob@vlab.org',
                               'machines': {'vm01': 'some info'},
                               'owner': 'bob',
                               'summary': 'Look at this cool template I made!'})

        self.assertEqual(the_args, expected)


class TestUpdateMeta(unittest.TestCase):
    """A set of test cases for the ``update_meta`` function"""

    @patch.object(template_meta_data, '_read_meta')
    @patch.object(template_meta_data, '_write_meta')
    def test_update_meta(self, fake_write_meta, fake_read_meta):
        """``template_meta_data`` - The update_meta does not change the 'machines'"""
        template = 'the best template ever'
        owner = 'bob'
        username = 'sam'
        email = 'bob@vlab.org'
        summary = "Look at this cool template I made!"
        fake_read_meta.return_value = {'owner' : "sam",
                                       "email": "sam@vlab.org",
                                       "summary": "my first template",
                                       "machines": {'vm01': "details"}}

        template_meta_data.update_meta(template, username=username, owner=owner, email=email, summary=summary)
        the_args, _ = fake_write_meta.call_args
        expected = ('the best template ever', {'owner': 'bob',
                                               'email': 'bob@vlab.org',
                                               'summary': 'Look at this cool template I made!',
                                               'machines': {'vm01': 'details'}})

        self.assertEqual(the_args, expected)

    @patch.object(template_meta_data, '_read_meta')
    @patch.object(template_meta_data, '_write_meta')
    def test_update_meta_valueerror(self, fake_write_meta, fake_read_meta):
        """``template_meta_data`` - The update_meta raises ValueError when the user does not own the template"""
        template = 'the best template ever'
        owner = 'bob'
        username = 'bob'
        email = 'bob@vlab.org'
        summary = "Look at this cool template I made!"
        fake_read_meta.return_value = {'owner' : "sam",
                                       "email": "sam@vlab.org",
                                       "summary": "my first template",
                                       "machines": {'vm01': "details"}}
        with self.assertRaises(ValueError):
            template_meta_data.update_meta(template, username=username, owner=owner, email=email, summary=summary)


class TestMapMachine(unittest.TestCase):
    """A set of test cases for the ``map_machine`` function"""

    def test_map_machine(self):
        """``template_meta_data`` - The map_machine function returns the expected dictionary"""
        name = 'vm01'
        ip = '1.2.3.4'
        kind = 'CoolestEverVM'
        ports = [22, 443]

        output = template_meta_data.map_machine(name, ip, kind, ports)
        expected = {'vm01' : {'ip' : ip, 'kind': kind, 'ports': ports}}

        self.assertEqual(output, expected)


class TestInternalFuncs(unittest.TestCase):
    """A set of test cases for the private/internal functions"""

    @patch.object(template_meta_data, 'open')
    def test_write_meta(self, fake_open):
        """``template_meta_data`` - _write_meta opens the correct file for writing"""
        meta = {'foo': 'bar'}
        template_meta_data._write_meta(template='foo', meta=meta)

        the_args, _ = fake_open.call_args
        expected = ('/templates/foo/meta.json', 'w')

        self.assertEqual(the_args, expected)

    @patch.object(template_meta_data, 'open')
    def test_read_meta(self, fake_open):
        """``template_meta_data`` - _read_meta returns the expected data"""
        fake_open.return_value.__enter__.return_value.read.return_value = '{"machines": {"someVM": {"ip": "1.2.3.4", "kind": "foo"}}}'

        meta = template_meta_data._read_meta(template='foo')
        expected = {'machines': {'someVM': {'ip': '1.2.3.4', 'kind': 'foo'}}}

        self.assertEqual(meta, expected)

    def test_get_template_path(self):
        """``template_meta_data`` - _get_template_path builds the expected file path"""
        output = template_meta_data._get_template_path(template='foo')
        expected = '/templates/foo/meta.json'

        self.assertEqual(output, expected)

    def test_get_template_path_hidden(self):
        """``template_meta_data`` - _get_template_path can generate a hidden path for the template"""
        output = template_meta_data._get_template_path(template='foo', hidden=True)
        expected = '/templates/.foo/meta.json'

        self.assertEqual(output, expected)


if __name__ == "__main__":
    unittest.main()
