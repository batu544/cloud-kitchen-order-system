"""Unit tests for security.py utilities."""
import unittest
from unittest.mock import patch
from src.utils.security import (
    hash_password, verify_password, 
    generate_jwt_token, decode_jwt_token,
    extract_token_from_header
)


class TestSecurityUtils(unittest.TestCase):

    def test_password_hashing(self):
        password = "secret_password"
        hashed = hash_password(password)
        
        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrong_password", hashed))

    def test_jwt_token_flow(self):
        user_id = 123
        username = "testuser"
        role = "admin"
        
        token = generate_jwt_token(user_id, username, role)
        self.assertIsInstance(token, str)
        
        decoded = decode_jwt_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded['user_id'], user_id)
        self.assertEqual(decoded['username'], username)
        self.assertEqual(decoded['role'], role)

    def test_jwt_token_with_cust_id(self):
        token = generate_jwt_token(1, "u", "r", cust_id=456)
        decoded = decode_jwt_token(token)
        self.assertEqual(decoded['cust_id'], 456)

    def test_decode_invalid_token(self):
        self.assertIsNone(decode_jwt_token("invalid.token.here"))

    def test_extract_token_from_header(self):
        # Valid header
        header = "Bearer my_precious_token"
        token = extract_token_from_header(header)
        self.assertEqual(token, "my_precious_token")
        
        # Case insensitive Bearer
        header = "bearer mixed_case_token"
        token = extract_token_from_header(header)
        self.assertEqual(token, "mixed_case_token")
        
        # Missing header
        self.assertIsNone(extract_token_from_header(None))
        
        # Invalid format
        self.assertIsNone(extract_token_from_header("NotBearer token"))
        self.assertIsNone(extract_token_from_header("Bearer"))
        self.assertIsNone(extract_token_from_header("Bearer too many parts"))


if __name__ == '__main__':
    unittest.main()
