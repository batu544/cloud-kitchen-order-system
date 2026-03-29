"""Order repository for order management."""
from typing import Optional, Dict, List
from decimal import Decimal
from src.repositories.base import BaseRepository
from src.database.connection import get_db_cursor, get_db_connection


class OrderRepository(BaseRepository):
    """Repository for order operations."""

    def __init__(self):
        super().__init__('kitch_order', 'order_id')

    def create_order_with_items(self, order_data: Dict, items: List[Dict]) -> Optional[int]:
        """
        Create order with items in a transaction (CRITICAL - SPEC.md lines 54-89).

        Args:
            order_data: Order data dictionary
            items: List of order item dictionaries

        Returns:
            New order ID or None if failed
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Insert order
                order_fields = list(order_data.keys())
                placeholders = ', '.join(['%s'] * len(order_fields))
                fields_str = ', '.join(order_fields)

                cursor.execute(
                    f"""
                    INSERT INTO kitch_order ({fields_str})
                    VALUES ({placeholders})
                    RETURNING order_id
                    """,
                    list(order_data.values())
                )
                order_id = cursor.fetchone()[0]

                # Insert order items
                for item in items:
                    item['order_id'] = order_id
                    item_fields = list(item.keys())
                    item_placeholders = ', '.join(['%s'] * len(item_fields))
                    item_fields_str = ', '.join(item_fields)

                    cursor.execute(
                        f"""
                        INSERT INTO kitch_order_item ({item_fields_str})
                        VALUES ({item_placeholders})
                        """,
                        list(item.values())
                    )

                # Create initial status history entry
                if 'current_status_id' in order_data and order_data['current_status_id']:
                    cursor.execute(
                        """
                        INSERT INTO kitch_order_status_history
                        (order_id, status_id, changed_by_user_id, note)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (order_id, order_data['current_status_id'],
                         order_data.get('placed_by_user_id'), 'Order created')
                    )

                conn.commit()
                return order_id

    def get_order_with_items(self, order_id: int) -> Optional[Dict]:
        """
        Get order with all items and customer info.

        Args:
            order_id: Order ID

        Returns:
            Order dictionary with items list
        """
        with get_db_cursor(commit=False) as cursor:
            # Get order with customer and status
            cursor.execute(
                """
                SELECT o.*, c.cust_name, s.status_name as current_status_name
                FROM kitch_order o
                LEFT JOIN kitch_customer c ON o.cust_id = c.cust_id
                LEFT JOIN kitch_status s ON o.current_status_id = s.status_id
                WHERE o.order_id = %s
                """,
                (order_id,)
            )
            order_row = cursor.fetchone()

            if not order_row:
                return None

            order = self._row_to_dict(cursor, order_row)

            # Get order items
            cursor.execute(
                """
                SELECT * FROM kitch_order_item
                WHERE order_id = %s
                ORDER BY order_item_id
                """,
                (order_id,)
            )
            item_rows = cursor.fetchall()
            order['items'] = self._rows_to_dicts(cursor, item_rows)

            return order

    def find_by_order_ref(self, order_ref: str) -> Optional[Dict]:
        """
        Find order by order reference (for tracking).

        Args:
            order_ref: Order reference string

        Returns:
            Order dictionary with items
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT o.*, c.cust_name, s.status_name as current_status_name
                FROM kitch_order o
                LEFT JOIN kitch_customer c ON o.cust_id = c.cust_id
                LEFT JOIN kitch_status s ON o.current_status_id = s.status_id
                WHERE o.order_ref = %s
                """,
                (order_ref,)
            )
            order_row = cursor.fetchone()

            if not order_row:
                return None

            order = self._row_to_dict(cursor, order_row)

            # Get order items
            cursor.execute(
                "SELECT * FROM kitch_order_item WHERE order_id = %s",
                (order['order_id'],)
            )
            item_rows = cursor.fetchall()
            order['items'] = self._rows_to_dicts(cursor, item_rows)

            return order

    def get_order_status_history(self, order_id: int) -> List[Dict]:
        """
        Get order status history with status names.

        Args:
            order_id: Order ID

        Returns:
            List of status history entries
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT h.*, s.status_name
                FROM kitch_order_status_history h
                LEFT JOIN kitch_status s ON h.status_id = s.status_id
                WHERE h.order_id = %s
                ORDER BY h.changed_at DESC
                """,
                (order_id,)
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)

    def update_order_status(self, order_id: int, status_id: int,
                           changed_by_user_id: int = None, note: str = None) -> bool:
        """
        Update order status and create history entry.

        Args:
            order_id: Order ID
            status_id: New status ID
            changed_by_user_id: User making the change
            note: Optional note

        Returns:
            True if successful
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Update order status
                cursor.execute(
                    """
                    UPDATE kitch_order
                    SET current_status_id = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE order_id = %s
                    """,
                    (status_id, order_id)
                )

                # Create history entry
                cursor.execute(
                    """
                    INSERT INTO kitch_order_status_history
                    (order_id, status_id, changed_by_user_id, note)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (order_id, status_id, changed_by_user_id, note)
                )

                conn.commit()
                return cursor.rowcount > 0

    def update_payment_status(self, order_id: int, payment_status: str) -> bool:
        """
        Update order payment status.

        Args:
            order_id: Order ID
            payment_status: New payment status

        Returns:
            True if successful
        """
        return self.update(order_id, {
            'payment_status': payment_status,
            'updated_at': 'CURRENT_TIMESTAMP'
        })

    def get_orders_by_customer(self, cust_id: int, limit: int = 20) -> List[Dict]:
        """
        Get orders for a specific customer.

        Args:
            cust_id: Customer ID
            limit: Maximum orders to return

        Returns:
            List of order dictionaries
        """
        with get_db_cursor(commit=False) as cursor:
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

    def get_orders_by_phone(self, phone: str, limit: int = 20) -> List[Dict]:
        """
        Get orders by phone number (for guest orders).

        Args:
            phone: Phone number
            limit: Maximum orders to return

        Returns:
            List of order dictionaries
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT o.*, s.status_name as current_status_name
                FROM kitch_order o
                LEFT JOIN kitch_status s ON o.current_status_id = s.status_id
                WHERE o.order_phone = %s
                ORDER BY o.order_date DESC
                LIMIT %s
                """,
                (phone, limit)
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)

    def get_recent_orders(self, limit: int = 50, status_id: int = None) -> List[Dict]:
        """
        Get recent orders with optional status filter.

        Args:
            limit: Maximum orders to return
            status_id: Optional status filter

        Returns:
            List of order dictionaries
        """
        query = """
            SELECT o.*, c.cust_name, s.status_name as current_status_name
            FROM kitch_order o
            LEFT JOIN kitch_customer c ON o.cust_id = c.cust_id
            LEFT JOIN kitch_status s ON o.current_status_id = s.status_id
            WHERE 1=1
        """
        params = []

        if status_id:
            query += " AND o.current_status_id = %s"
            params.append(status_id)

        query += " ORDER BY o.order_date DESC LIMIT %s"
        params.append(limit)

        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)

    def get_all_statuses(self) -> List[Dict]:
        """
        Get all order statuses.

        Returns:
            List of status dictionaries
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM kitch_status ORDER BY display_order"
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)
