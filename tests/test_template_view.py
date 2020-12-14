# -*- coding: UTF-8 -*-
"""
A suite of tests for the template object
"""
import unittest
from unittest.mock import patch, MagicMock

import ujson
from flask import Flask
from vlab_api_common import flask_common
from vlab_api_common.http_auth import generate_v2_test_token

from vlab_deployment_api.lib.views import deployment


class TestTemplateView(unittest.TestCase):
    """A set of test cases for the TemplateView object"""
    @classmethod
    def setUpClass(cls):
        """Runs once for the whole test suite"""
        cls.token = generate_v2_test_token(username='bob')

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        app = Flask(__name__)
        deployment.TemplateView.register(app)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        # Mock Celery
        app.celery_app = MagicMock()
        cls.fake_task = MagicMock()
        cls.fake_task.id = 'asdf-asdf-asdf'
        app.celery_app.send_task.return_value = cls.fake_task


    def test_v1_deprecated(self):
        """TemplateView - GET on /api/1/inf/template returns an HTTP 404"""
        resp = self.app.get('/api/1/inf/template',
                            headers={'X-Auth': self.token})

        status = resp.status_code
        expected = 404

        self.assertEqual(status, expected)

    def test_get_task(self):
        """TemplateView - GET on /api/2/inf/template returns a task-id"""
        resp = self.app.get('/api/2/inf/template',
                            headers={'X-Auth': self.token})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_get_task_link(self):
        """TemplateView - GET on /api/2/inf/template sets the Link header"""
        resp = self.app.get('/api/2/inf/template',
                            headers={'X-Auth': self.token})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/2/inf/template/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_post_task(self):
        """TemplateView - POST on /api/2/inf/template returns a task-id"""
        the_json = {"machines" : ['myVM01'],
                    "portmaps" : [{"name": "myVM01", 'target_addr' : "1.2.3.4", 'target_ports': [22]}],
                    "summary" : "This is what my template is all about!",
                    "name" : 'myNewTemplate'
                   }
        resp = self.app.post('/api/2/inf/template',
                             headers={'X-Auth': self.token},
                             json=the_json)

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_post_task_link(self):
        """TemplateView - POST on /api/2/inf/template sets the Link header"""
        the_json = {"machines" : ['myVM01'],
                    "portmaps" : [{"name": "myVM01", 'target_addr' : "1.2.3.4", 'target_ports': [22]}],
                    "summary" : "This is what my template is all about!",
                    "name" : 'myNewTemplate'
                   }
        resp = self.app.post('/api/2/inf/template',
                             headers={'X-Auth': self.token},
                             json=the_json)

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/2/inf/template/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_post_schema(self):
        """TemplateView - POST returns an HTTP 400 error when supplied with junk data"""
        resp = self.app.post('/api/2/inf/template',
                             headers={'X-Auth': self.token},
                             json={'some' : 'junk'})
        expected = 400

        self.assertEqual(expected, resp.status_code)

    def test_delete_task(self):
        """TemplateView - DELETE on /api/2/inf/template returns a task-id"""
        resp = self.app.delete('/api/2/inf/template',
                               headers={'X-Auth': self.token},
                               json={'template' : 'mytemplate'})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_delete_task_link(self):
        """TemplateView - DELETE on /api/2/inf/template sets the Link header"""
        resp = self.app.delete('/api/2/inf/template',
                               headers={'X-Auth': self.token},
                               json={'template' : 'mytemplate'})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/2/inf/template/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_put_task(self):
        """TemplateView - PUT on /api/2/inf/template returns a task-id"""
        resp = self.app.delete('/api/2/inf/template',
                               headers={'X-Auth': self.token},
                               json={'template' : 'mytemplate', 'owner' : "newOwner"})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_put_task_link(self):
        """TemplateView - PUT on /api/2/inf/template sets the Link header"""
        resp = self.app.put('/api/2/inf/template',
                               headers={'X-Auth': self.token},
                               json={'template' : 'mytemplate', 'owner' : "newOwner", 'summary' : 'some blurb about this template',})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/2/inf/template/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_put_requires_template(self):
        """TemplateView - PUT on /api/2/inf/template requires the user to specify which template to modify"""
        resp = self.app.put('/api/2/inf/template',
                               headers={'X-Auth': self.token},
                               json={'summary' : 'some blurb about this template', 'owner' : "newOwner"})

        expected = 400

        self.assertEqual(resp.status_code, expected)


if __name__ == '__main__':
    unittest.main()
