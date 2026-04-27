"""Unit tests for auth_middleware decorators."""
import unittest
from unittest.mock import MagicMock, patch
from flask import Flask, g
from src.middleware.auth_middleware import require_auth, require_role, optional_auth


class TestMiddleware(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @patch('src.middleware.auth_middleware.extract_token_from_header')
    @patch('src.middleware.auth_middleware.decode_jwt_token')
    def test_require_auth_success(self, mock_decode, mock_extract):
        mock_extract.return_value = 'valid_token'
        mock_decode.return_value = {'user_id': 1, 'role': 'staff'}

        with self.app.test_request_context(headers={'Authorization': 'Bearer valid_token'}):
            @require_auth
            def test_func():
                return "ok"

            result = test_func()
            self.assertEqual(result, "ok")
            self.assertEqual(g.current_user['user_id'], 1)

    @patch('src.middleware.auth_middleware.extract_token_from_header')
    def test_require_auth_missing_token(self, mock_extract):
        mock_extract.return_value = None

        with self.app.test_request_context():
            @require_auth
            def test_func():
                return "ok"

            resp, status = test_func()
            self.assertEqual(status, 401)

    @patch('src.middleware.auth_middleware.extract_token_from_header')
    @patch('src.middleware.auth_middleware.decode_jwt_token')
    def test_require_auth_invalid_token(self, mock_decode, mock_extract):
        mock_extract.return_value = 'bad_token'
        mock_decode.return_value = None

        with self.app.test_request_context(headers={'Authorization': 'Bearer bad_token'}):
            @require_auth
            def test_func():
                return "ok"

            resp, status = test_func()
            self.assertEqual(status, 401)

    def test_require_role_success(self):
        with self.app.test_request_context():
            g.current_user = {'role': 'admin'}

            @require_role('admin', 'staff')
            def test_func():
                return "ok"

            result = test_func()
            self.assertEqual(result, "ok")

    def test_require_role_forbidden(self):
        with self.app.test_request_context():
            g.current_user = {'role': 'customer'}

            @require_role('admin', 'staff')
            def test_func():
                return "ok"

            resp, status = test_func()
            self.assertEqual(status, 403)

    @patch('src.middleware.auth_middleware.extract_token_from_header')
    @patch('src.middleware.auth_middleware.decode_jwt_token')
    def test_optional_auth_present(self, mock_decode, mock_extract):
        mock_extract.return_value = 'token'
        mock_decode.return_value = {'user_id': 2}
        
        with self.app.test_request_context(headers={'Authorization': 'Bearer token'}):
            @optional_auth
            def test_func():
                return "ok"

            test_func()
            self.assertEqual(g.current_user['user_id'], 2)

    @patch('src.middleware.auth_middleware.extract_token_from_header')
    def test_optional_auth_missing(self, mock_extract):
        mock_extract.return_value = None
        
        with self.app.test_request_context():
            if hasattr(g, 'current_user'):
                del g.current_user

            @optional_auth
            def test_func():
                return "ok"

            test_func()
            self.assertFalse(hasattr(g, 'current_user'))


if __name__ == '__main__':
    unittest.main()
