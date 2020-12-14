# -*- coding: UTF-8 -*-
"""
A suite of tests for the HTTP API schemas
"""
import unittest

from jsonschema import Draft4Validator, validate, ValidationError
from vlab_deployment_api.lib.views import deployment


class TestDeploymentViewSchema(unittest.TestCase):
    """A set of test cases for the schemas of /api/2/inf/deployment"""

    def test_post_schema(self):
        """The schema defined for POST on is valid"""
        try:
            Draft4Validator.check_schema(deployment.DeploymentView.POST_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)


    def test_get_schema(self):
        """The schema defined for GET on is valid"""
        try:
            Draft4Validator.check_schema(deployment.DeploymentView.GET_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_delete_schema(self):
        """The schema defined for DELETE on is valid"""
        try:
            Draft4Validator.check_schema(deployment.DeploymentView.DELETE_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_templates_schema(self):
        """The schema defined for GET on /template is valid"""
        try:
            Draft4Validator.check_schema(deployment.DeploymentView.TEMPLATES_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)


class TestTemplateViewSchema(unittest.TestCase):
    """A set of test cases for the schemas of /api/2/inf/template"""

    def test_post_schema(self):
        """The schema defined for POST is on /api/2/inf/template valid"""
        try:
            Draft4Validator.check_schema(deployment.TemplateView.POST_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_get_schema(self):
        """The schema defined for GET is on /api/2/inf/template valid"""
        try:
            Draft4Validator.check_schema(deployment.TemplateView.GET_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_delete_schema(self):
        """The schema defined for DELETE on /api/2/inf/template is valid"""
        try:
            Draft4Validator.check_schema(deployment.TemplateView.DELETE_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_put_schema(self):
        """The schema defined for PUT on /api/2/inf/template is valid"""
        try:
            Draft4Validator.check_schema(deployment.TemplateView.PUT_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)


if __name__ == '__main__':
    unittest.main()
