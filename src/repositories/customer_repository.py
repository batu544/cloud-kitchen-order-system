"""Customer repository."""
from typing import Optional, Dict, List
from datetime import datetime
from src.repositories.base import BaseRepository
from src.database.connection import get_db_cursor


class CustomerRepository(BaseRepository):
    """Repository for customer operations."""

    def __init__(self):
        super().__init__('kitch_customer', 'cust_id')

    def find_by_phone(self, phone: str) -> Optional[Dict]:
        """
        Find customer by phone number (SPEC.md line 26 - staff phone lookup).

        Args:
            phone: Phone number (10 digits)

        Returns:
            Customer dictionary or None if not found
        """
        return self.find_by_field('cust_phone_number', phone)

    def find_by_email(self, email: str) -> Optional[Dict]:
        """
        Find customer by email.

        Args:
            email: Email address

        Returns:
            Customer dictionary or None if not found
        """
        return self.find_by_field('cust_email', email)

    def create_customer(self, name: str, phone: str, email: str = None,
                       address: str = None) -> Optional[int]:
        """
        Create a new customer.

        Args:
            name: Customer name
            phone: Phone number (10 digits)
            email: Optional email
            address: Optional address

        Returns:
            New customer ID or None if creation failed
        """
        data = {
            'cust_name': name,
            'cust_phone_number': phone,
            'cust_email': email,
            'cust_address': address
        }
        return self.insert(data)

    def update_customer(self, cust_id: int, name: str = None, email: str = None,
                       address: str = None) -> bool:
        """
        Update customer information.

        Args:
            cust_id: Customer ID
            name: Optional new name
            email: Optional new email
            address: Optional new address

        Returns:
            True if successful
        """
        data = {'updated_at': datetime.now()}
        if name:
            data['cust_name'] = name
        if email:
            data['cust_email'] = email
        if address:
            data['cust_address'] = address

        return self.update(cust_id, data)

    def get_customer_order_history(self, cust_id: int, limit: int = 10) -> List[Dict]:
        """
        Get customer's order history.

        Args:
            cust_id: Customer ID
            limit: Maximum number of orders to return

        Returns:
            List of order dictionaries
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT o.*, s.status_name as current_status_name
                FROM kitch_order o
                LEFT JOIN kitch_status s ON o.current_status_id = s.status_id
                WHERE o.cust_id = %s
                ORDER BY o.order_date DESC
                LIMIT %s
                """,
                (cust_id, limit)
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)

    def search_customers(self, search_term: str, limit: int = 20) -> List[Dict]:
        """
        Search customers by name or phone.

        Args:
            search_term: Search term
            limit: Maximum results

        Returns:
            List of matching customer dictionaries
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM kitch_customer
                WHERE cust_name ILIKE %s OR cust_phone_number LIKE %s
                ORDER BY cust_name
                LIMIT %s
                """,
                (f'%{search_term}%', f'%{search_term}%', limit)
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)
