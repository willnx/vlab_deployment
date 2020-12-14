# -*- coding: UTF-8 -*-
"""
A suite of tests for the deployment object
"""
import unittest
from unittest.mock import patch, MagicMock

import ujson
from flask import Flask
from vlab_api_common import flask_common
from vlab_api_common.http_auth import generate_v2_test_token


from vlab_deployment_api.lib.views import deployment


class TestDeploymentView(unittest.TestCase):
    """A set of test cases for the DeploymentView object"""
    @classmethod
    def setUpClass(cls):
        """Runs once for the whole test suite"""
        cls.token = generate_v2_test_token(username='bob')

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        app = Flask(__name__)
        deployment.DeploymentView.register(app)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        # Mock Celery
        app.celery_app = MagicMock()
        cls.fake_task = MagicMock()
        cls.fake_task.id = 'asdf-asdf-asdf'
        cls.celery_app = app.celery_app
        app.celery_app.send_task.return_value = cls.fake_task

    def test_v1_deprecated(self):
        """DeploymentView - GET on /api/1/inf/deployment returns an HTTP 404"""
        resp = self.app.get('/api/1/inf/deployment',
                            headers={'X-Auth': self.token})

        status = resp.status_code
        expected = 404

        self.assertEqual(status, expected)

    def test_get_task(self):
        """DeploymentView - GET on /api/2/inf/deployment returns a task-id"""
        resp = self.app.get('/api/2/inf/deployment',
                            headers={'X-Auth': self.token})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_get_task_link(self):
        """DeploymentView - GET on /api/2/inf/deployment sets the Link header"""
        resp = self.app.get('/api/2/inf/deployment',
                            headers={'X-Auth': self.token})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/2/inf/deployment/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_post_task(self):
        """DeploymentView - POST on /api/2/inf/deployment returns a task-id"""
        resp = self.app.post('/api/2/inf/deployment',
                             headers={'X-Auth': self.token},
                             json={'network': "someLAN",
                                   'template': "myDeployment"})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_post_task_link(self):
        """DeploymentView - POST on /api/2/inf/deployment sets the Link header"""
        resp = self.app.post('/api/2/inf/deployment',
                             headers={'X-Auth': self.token},
                             json={'network': "someLAN",
                                   'template': "myDeployment"})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/2/inf/deployment/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_delete_task(self):
        """DeploymentView - DELETE on /api/2/inf/deployment returns a task-id"""
        resp = self.app.delete('/api/2/inf/deployment',
                               headers={'X-Auth': self.token},
                               json={'template' : 'myDeployment'})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_delete_task_link(self):
        """DeploymentView - DELETE on /api/2/inf/deployment sets the Link header"""
        resp = self.app.delete('/api/2/inf/deployment',
                               headers={'X-Auth': self.token},
                               json={'template' : 'myDeployment'})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/2/inf/deployment/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_image(self):
        """DeploymentView - GET on the ./image end point returns the a task-id"""
        resp = self.app.get('/api/2/inf/deployment/image',
                            headers={'X-Auth': self.token})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_image(self):
        """DeploymentView - GET on the ./image end point sets the Link header"""
        resp = self.app.get('/api/2/inf/deployment/image',
                            headers={'X-Auth': self.token})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/2/inf/deployment/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_image_verbose(self):
        """TemplateView - GET on /api/2/inf/deployment/image supports the 'verbose=true' argument"""
        resp = self.app.get('/api/2/inf/deployment/image?verbose=true',
                            headers={'X-Auth': self.token})
        the_args = self.celery_app.send_task.call_args[0]
        expected = ('deployment.images', [True, 'noId'])

        self.assertEqual(the_args, expected)

if __name__ == '__main__':
    unittest.main()
