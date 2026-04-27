"""Unit tests for responses.py utilities."""
import unittest
from flask import Flask
import json
from src.utils.responses import (
    success_response, error_response, validation_error_response,
    not_found_response, unauthorized_response, forbidden_response
)


class TestResponseUtils(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_success_response(self):
        data = {'id': 1}
        resp, status = success_response(data=data, message="Cool")
        
        self.assertEqual(status, 200)
        body = json.loads(resp.data)
        self.assertTrue(body['success'])
        self.assertEqual(body['message'], "Cool")
        self.assertEqual(body['data'], data)

    def test_error_response(self):
        resp, status = error_response(message="Failed", status_code=403, errors={'field': 'err'})
        
        self.assertEqual(status, 403)
        body = json.loads(resp.data)
        self.assertFalse(body['success'])
        self.assertEqual(body['message'], "Failed")
        self.assertEqual(body['errors'], {'field': 'err'})

    def test_validation_error_response(self):
        errors = {'email': 'invalid'}
        resp, status = validation_error_response(errors)
        
        self.assertEqual(status, 400)
        body = json.loads(resp.data)
        self.assertEqual(body['message'], "Validation failed")
        self.assertEqual(body['errors'], errors)

    def test_not_found_response(self):
        resp, status = not_found_response("User")
        self.assertEqual(status, 404)
        body = json.loads(resp.data)
        self.assertEqual(body['message'], "User not found")

    def test_unauthorized_response(self):
        resp, status = unauthorized_response("Go away")
        self.assertEqual(status, 401)
        body = json.loads(resp.data)
        self.assertEqual(body['message'], "Go away")

    def test_forbidden_response(self):
        resp, status = forbidden_response("No entry")
        self.assertEqual(status, 403)
        body = json.loads(resp.data)
        self.assertEqual(body['message'], "No entry")


if __name__ == '__main__':
    unittest.main()
