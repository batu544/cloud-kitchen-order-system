"""Authentication service for user registration and login."""
from typing import Optional, Dict, Tuple
from src.repositories.user_repository import UserRepository
from src.repositories.customer_repository import CustomerRepository
from src.utils.security import hash_password, verify_password, generate_jwt_token
from src.utils.validators import validate_email, validate_phone


class AuthService:
    """Service for authentication operations."""

    def __init__(self):
        self.user_repo = UserRepository()
        self.customer_repo = CustomerRepository()

    def register_user(self, username: str, password: str, phone: str,
                     cust_name: str, email: str = None, address: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Register a new user account.

        Args:
            username: Username (email format recommended)
            password: Plain text password
            phone: Phone number (10 digits)
            cust_name: Customer name
            email: Optional email (if different from username)
            address: Optional address

        Returns:
            Tuple of (success, message, user_data_with_token)
        """
        # Validate username (must not be empty, min 3 chars)
        if not username or len(username.strip()) < 3:
            return False, "Username must be at least 3 characters", None

        # Validate optional email if provided
        if email and email.strip():
            is_valid_email, email_error = validate_email(email)
            if not is_valid_email:
                return False, email_error, None

        # Validate phone
        is_valid_phone, phone_result = validate_phone(phone)
        if not is_valid_phone:
            return False, phone_result, None

        normalized_phone = phone_result

        # Check if username already exists
        existing_user = self.user_repo.find_by_username(username)
        if existing_user:
            return False, "Username already exists", None

        # Check if customer with phone already exists
        existing_customer = self.customer_repo.find_by_phone(normalized_phone)

        try:
            # Create or get customer
            if existing_customer:
                cust_id = existing_customer['cust_id']
            else:
                cust_id = self.customer_repo.create_customer(
                    name=cust_name,
                    phone=normalized_phone,
                    email=email if email and email.strip() else None,
                    address=address
                )

            if not cust_id:
                return False, "Failed to create customer record", None

            # Hash password
            password_hash = hash_password(password)

            # Create user
            user_id = self.user_repo.create_user(
                username=username,
                password_hash=password_hash,
                role='customer',
                cust_id=cust_id
            )

            if not user_id:
                return False, "Failed to create user account", None

            # Generate JWT token
            token = generate_jwt_token(user_id, username, 'customer')

            user_data = {
                'user_id': user_id,
                'username': username,
                'role': 'customer',
                'cust_id': cust_id,
                'token': token
            }

            return True, "Registration successful", user_data

        except Exception as e:
            return False, f"Registration failed: {str(e)}", None

    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user and generate JWT token.

        Args:
            username: Username
            password: Plain text password

        Returns:
            Tuple of (success, message, user_data_with_token)
        """
        # Find user
        user = self.user_repo.find_by_username(username)

        if not user:
            return False, "Invalid username or password", None

        # Check if user is active
        if not user.get('is_active', False):
            return False, "Account is inactive", None

        # Verify password
        if not verify_password(password, user['password_hash']):
            return False, "Invalid username or password", None

        # Generate JWT token
        token = generate_jwt_token(
            user['user_id'],
            user['username'],
            user['role']
        )

        user_data = {
            'user_id': user['user_id'],
            'username': user['username'],
            'role': user['role'],
            'cust_id': user.get('cust_id'),
            'token': token
        }

        return True, "Login successful", user_data

    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """
        Get user information with customer details.

        Args:
            user_id: User ID

        Returns:
            User dictionary with customer info or None
        """
        return self.user_repo.get_user_with_customer(user_id)

    def change_password(self, user_id: int, current_password: str,
                       new_password: str) -> Tuple[bool, str]:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            Tuple of (success, message)
        """
        # Get user
        user = self.user_repo.find_by_id(user_id)
        if not user:
            return False, "User not found"

        # Verify current password
        if not verify_password(current_password, user['password_hash']):
            return False, "Current password is incorrect"

        # Hash new password
        new_password_hash = hash_password(new_password)

        # Update password
        success = self.user_repo.update_password(user_id, new_password_hash)

        if success:
            return True, "Password updated successfully"
        else:
            return False, "Failed to update password"
