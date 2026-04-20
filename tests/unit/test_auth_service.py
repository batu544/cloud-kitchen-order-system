"""Unit tests for auth_service.py with mocked repositories."""
import unittest
from unittest.mock import MagicMock, patch


class TestAuthServiceRegister(unittest.TestCase):

    def setUp(self):
        # Patch repositories and security utilities so no DB is needed
        self.user_repo_patcher = patch('src.services.auth_service.UserRepository')
        self.cust_repo_patcher = patch('src.services.auth_service.CustomerRepository')
        self.hash_patcher = patch('src.services.auth_service.hash_password', return_value='hashed_pw')
        self.jwt_patcher = patch('src.services.auth_service.generate_jwt_token', return_value='test_token')

        self.MockUserRepo = self.user_repo_patcher.start()
        self.MockCustRepo = self.cust_repo_patcher.start()
        self.hash_patcher.start()
        self.jwt_patcher.start()

        self.mock_user_repo = MagicMock()
        self.mock_cust_repo = MagicMock()
        self.MockUserRepo.return_value = self.mock_user_repo
        self.MockCustRepo.return_value = self.mock_cust_repo

        from src.services.auth_service import AuthService
        self.service = AuthService()

    def tearDown(self):
        self.user_repo_patcher.stop()
        self.cust_repo_patcher.stop()
        self.hash_patcher.stop()
        self.jwt_patcher.stop()

    def test_register_success_new_customer(self):
        self.mock_user_repo.find_by_username.return_value = None
        self.mock_cust_repo.find_by_phone.return_value = None
        self.mock_cust_repo.create_customer.return_value = 10
        self.mock_user_repo.create_user.return_value = 1

        ok, msg, data = self.service.register_user(
            username='testuser',
            password='pass1234',
            phone='1234567890',
            cust_name='Test User'
        )

        self.assertTrue(ok)
        self.assertIsNotNone(data)
        self.assertEqual(data['token'], 'test_token')
        self.mock_cust_repo.create_customer.assert_called_once()

    def test_register_existing_customer_linked(self):
        self.mock_user_repo.find_by_username.return_value = None
        self.mock_cust_repo.find_by_phone.return_value = {'cust_id': 5, 'cust_name': 'Existing'}
        self.mock_user_repo.find_by_customer_id.return_value = None
        self.mock_user_repo.create_user.return_value = 2

        ok, msg, data = self.service.register_user(
            username='testuser',
            password='pass1234',
            phone='1234567890',
            cust_name='Test User'
        )

        self.assertTrue(ok)
        # create_customer must NOT be called since phone matched existing customer
        self.mock_cust_repo.create_customer.assert_not_called()
        self.assertEqual(data['cust_id'], 5)

    def test_register_duplicate_username(self):
        self.mock_user_repo.find_by_username.return_value = {'user_id': 1, 'username': 'testuser'}

        ok, msg, data = self.service.register_user(
            username='testuser',
            password='pass1234',
            phone='1234567890',
            cust_name='Test User'
        )

        self.assertFalse(ok)
        self.assertIn('already', msg.lower())
        self.assertIsNone(data)

    def test_register_invalid_phone(self):
        ok, msg, data = self.service.register_user(
            username='testuser',
            password='pass1234',
            phone='123',  # too short
            cust_name='Test User'
        )

        self.assertFalse(ok)
        self.assertIsNone(data)

    def test_register_invalid_email(self):
        self.mock_user_repo.find_by_username.return_value = None

        ok, msg, data = self.service.register_user(
            username='testuser',
            password='pass1234',
            phone='1234567890',
            cust_name='Test User',
            email='not-an-email'
        )

        self.assertFalse(ok)
        self.assertIsNone(data)

    def test_register_username_too_short(self):
        ok, msg, data = self.service.register_user(
            username='ab',  # less than 3 chars
            password='pass1234',
            phone='1234567890',
            cust_name='Test User'
        )

        self.assertFalse(ok)
        self.assertIsNone(data)


class TestAuthServiceLogin(unittest.TestCase):

    def setUp(self):
        self.user_repo_patcher = patch('src.services.auth_service.UserRepository')
        self.cust_repo_patcher = patch('src.services.auth_service.CustomerRepository')
        self.verify_patcher = patch('src.services.auth_service.verify_password')
        self.jwt_patcher = patch('src.services.auth_service.generate_jwt_token', return_value='test_token')

        self.MockUserRepo = self.user_repo_patcher.start()
        self.cust_repo_patcher.start()
        self.mock_verify = self.verify_patcher.start()
        self.jwt_patcher.start()

        self.mock_user_repo = MagicMock()
        self.MockUserRepo.return_value = self.mock_user_repo

        from src.services.auth_service import AuthService
        self.service = AuthService()

    def tearDown(self):
        self.user_repo_patcher.stop()
        self.cust_repo_patcher.stop()
        self.verify_patcher.stop()
        self.jwt_patcher.stop()

    def _make_user(self):
        return {
            'user_id': 1,
            'username': 'testuser',
            'password_hash': 'hashed_pw',
            'role': 'customer',
            'cust_id': 5,
            'is_active': True,
        }

    def test_login_success(self):
        self.mock_user_repo.find_by_username.return_value = self._make_user()
        self.mock_verify.return_value = True

        ok, msg, data = self.service.login('testuser', 'pass123')

        self.assertTrue(ok)
        self.assertEqual(data['token'], 'test_token')
        self.assertEqual(data['username'], 'testuser')

    def test_login_user_not_found(self):
        self.mock_user_repo.find_by_username.return_value = None

        ok, msg, data = self.service.login('nobody', 'pass')

        self.assertFalse(ok)
        self.assertIn('Invalid', msg)
        self.assertIsNone(data)

    def test_login_wrong_password(self):
        self.mock_user_repo.find_by_username.return_value = self._make_user()
        self.mock_verify.return_value = False

        ok, msg, data = self.service.login('testuser', 'wrongpass')

        self.assertFalse(ok)
        self.assertIn('Invalid', msg)
        self.assertIsNone(data)

    def test_login_inactive_account(self):
        user = self._make_user()
        user['is_active'] = False
        self.mock_user_repo.find_by_username.return_value = user

        ok, msg, data = self.service.login('testuser', 'pass123')

        self.assertFalse(ok)
        self.assertIn('inactive', msg.lower())
        self.assertIsNone(data)


class TestAuthServiceChangePassword(unittest.TestCase):

    def setUp(self):
        self.user_repo_patcher = patch('src.services.auth_service.UserRepository')
        self.cust_repo_patcher = patch('src.services.auth_service.CustomerRepository')
        self.verify_patcher = patch('src.services.auth_service.verify_password')
        self.hash_patcher = patch('src.services.auth_service.hash_password', return_value='new_hash')

        self.MockUserRepo = self.user_repo_patcher.start()
        self.cust_repo_patcher.start()
        self.mock_verify = self.verify_patcher.start()
        self.hash_patcher.start()

        self.mock_user_repo = MagicMock()
        self.MockUserRepo.return_value = self.mock_user_repo

        from src.services.auth_service import AuthService
        self.service = AuthService()

    def tearDown(self):
        self.user_repo_patcher.stop()
        self.cust_repo_patcher.stop()
        self.verify_patcher.stop()
        self.hash_patcher.stop()

    def test_change_password_success(self):
        self.mock_user_repo.find_by_id.return_value = {'user_id': 1, 'password_hash': 'old_hash'}
        self.mock_verify.return_value = True
        self.mock_user_repo.update_password.return_value = True

        ok, msg = self.service.change_password(1, 'old_pass', 'new_pass')

        self.assertTrue(ok)
        self.mock_user_repo.update_password.assert_called_once_with(1, 'new_hash')

    def test_change_password_wrong_current(self):
        self.mock_user_repo.find_by_id.return_value = {'user_id': 1, 'password_hash': 'old_hash'}
        self.mock_verify.return_value = False

        ok, msg = self.service.change_password(1, 'wrong_pass', 'new_pass')

        self.assertFalse(ok)
        self.assertIn('incorrect', msg.lower())

    def test_change_password_user_not_found(self):
        self.mock_user_repo.find_by_id.return_value = None

        ok, msg = self.service.change_password(99, 'old_pass', 'new_pass')

        self.assertFalse(ok)
        self.assertIn('not found', msg.lower())


if __name__ == '__main__':
    unittest.main()
