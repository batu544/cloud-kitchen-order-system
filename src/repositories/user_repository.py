"""User repository for authentication and user management."""
from typing import Optional, Dict
from datetime import datetime
from src.repositories.base import BaseRepository
from src.database.connection import get_db_cursor


class UserRepository(BaseRepository):
    """Repository for user operations."""

    def __init__(self):
        super().__init__('kitch_user', 'user_id')

    def find_by_username(self, username: str) -> Optional[Dict]:
        """
        Find user by username.

        Args:
            username: Username to search for

        Returns:
            User dictionary or None if not found
        """
        return self.find_by_field('username', username)

    def find_by_phone(self, phone: str) -> list:
        """
        Find all users linked to a customer with the given phone number.

        Returns:
            List of user dicts (empty, one, or multiple)
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT u.*
                FROM kitch_user u
                JOIN kitch_customer c ON u.cust_id = c.cust_id
                WHERE c.cust_phone_number = %s AND u.is_active = TRUE
                """,
                (phone,)
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)

    def find_by_customer_id(self, cust_id: int) -> Optional[Dict]:
        """
        Find user by customer ID.

        Args:
            cust_id: Customer ID

        Returns:
            User dictionary or None if not found
        """
        return self.find_by_field('cust_id', cust_id)

    def create_user(self, username: str, password_hash: str, role: str = 'customer',
                    cust_id: int = None) -> Optional[int]:
        """
        Create a new user.

        Args:
            username: Username (email)
            password_hash: Hashed password
            role: User role (customer, staff, admin)
            cust_id: Optional customer ID to link

        Returns:
            New user ID or None if creation failed
        """
        data = {
            'username': username,
            'password_hash': password_hash,
            'role': role,
            'cust_id': cust_id,
            'is_active': True
        }
        return self.insert(data)

    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """
        Update user password.

        Args:
            user_id: User ID
            new_password_hash: New hashed password

        Returns:
            True if successful
        """
        return self.update(user_id, {
            'password_hash': new_password_hash,
            'updated_at': datetime.now()
        })

    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        return self.update(user_id, {'is_active': False})

    def activate_user(self, user_id: int) -> bool:
        """
        Activate a user account.

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        return self.update(user_id, {'is_active': True})

    def get_all_users(self) -> list:
        """Return all users with their linked customer info."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT u.user_id, u.username, u.role, u.is_active, u.created_at,
                       c.cust_name, c.cust_phone_number, c.cust_email
                FROM kitch_user u
                LEFT JOIN kitch_customer c ON u.cust_id = c.cust_id
                ORDER BY u.created_at DESC
                """
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)

    def update_user(self, user_id: int, data: dict) -> bool:
        """Update allowed user fields (role, is_active)."""
        return self.update(user_id, data)

    def delete_user(self, user_id: int) -> bool:
        """Permanently delete a user record."""
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM kitch_user WHERE user_id = %s", (user_id,))
            return cursor.rowcount > 0

    def get_user_with_customer(self, user_id: int) -> Optional[Dict]:
        """
        Get user with joined customer information.

        Args:
            user_id: User ID

        Returns:
            Dictionary with user and customer data
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT u.*, c.cust_name, c.cust_phone_number, c.cust_email
                FROM kitch_user u
                LEFT JOIN kitch_customer c ON u.cust_id = c.cust_id
                WHERE u.user_id = %s
                """,
                (user_id,)
            )
            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)
