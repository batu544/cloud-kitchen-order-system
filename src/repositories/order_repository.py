"""Order repository for order management."""
from typing import Optional, Dict, List
from decimal import Decimal
from datetime import datetime
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

    def find_order_item_by_id(self, order_item_id: int) -> Optional[Dict]:
        """
        Find an order item by its ID.

        Args:
            order_item_id: Order item ID

        Returns:
            Order item dictionary or None
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM kitch_order_item WHERE order_item_id = %s",
                (order_item_id,)
            )
            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)

    def find_by_id_for_tracking(self, order_id: int) -> Optional[Dict]:
        """
        Find order by ID with full details for tracking (joins customer, status, items).

        Args:
            order_id: Order ID

        Returns:
            Order dictionary with items or None
        """
        with get_db_cursor(commit=False) as cursor:
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

            cursor.execute(
                "SELECT * FROM kitch_order_item WHERE order_id = %s",
                (order['order_id'],)
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
                # Check if cancelling — need to know current payment status
                cancelled_status_name = None
                cursor.execute(
                    "SELECT status_name FROM kitch_status WHERE status_id = %s",
                    (status_id,)
                )
                row = cursor.fetchone()
                if row:
                    cancelled_status_name = row[0]

                # Update order status (also set payment_status=refunded when cancelling)
                if cancelled_status_name == 'Cancelled':
                    cursor.execute(
                        """
                        UPDATE kitch_order
                        SET current_status_id = %s, payment_status = 'refunded',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE order_id = %s
                        """,
                        (status_id, order_id)
                    )
                else:
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
            'updated_at': datetime.now()
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

    def get_orders_paginated(
        self,
        page: int = 1,
        per_page: int = 10,
        date_filter: str = None,
        status_filter: int = None,
        order_by: str = 'order_date DESC'
    ) -> Dict:
        """
        Get orders with pagination and filters for staff dashboard.

        Args:
            page: Page number (1-indexed)
            per_page: Items per page (max 50)
            date_filter: ISO date string (YYYY-MM-DD) to filter by day
            status_filter: Status ID to filter by
            order_by: ORDER BY clause (default: order_date DESC)

        Returns:
            Dictionary with orders, total, page, per_page, total_pages
        """
        # Limit per_page to prevent excessive queries
        per_page = min(per_page, 50)
        offset = (page - 1) * per_page

        # Build query with filters
        where_clauses = []
        params = []

        if date_filter:
            where_clauses.append("DATE_TRUNC('day', o.order_date) = DATE_TRUNC('day', %s::timestamp)")
            params.append(date_filter)

        if status_filter:
            where_clauses.append("o.current_status_id = %s")
            params.append(status_filter)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_db_cursor(commit=False) as cursor:
            # Get total count with window function
            cursor.execute(f"""
                SELECT
                    o.order_id,
                    o.order_ref,
                    o.cust_id,
                    o.order_phone,
                    o.order_date,
                    o.subtotal,
                    o.discount_amount,
                    o.tip_amount,
                    o.tax_amount,
                    o.total_amount,
                    o.payment_status,
                    o.current_status_id,
                    o.notes,
                    c.cust_name,
                    s.status_name as current_status_name,
                    (SELECT COUNT(*) FROM kitch_order_item WHERE order_id = o.order_id) as item_count,
                    COUNT(*) OVER() as total_count
                FROM kitch_order o
                LEFT JOIN kitch_customer c ON o.cust_id = c.cust_id
                LEFT JOIN kitch_status s ON o.current_status_id = s.status_id
                WHERE {where_sql}
                ORDER BY {order_by}
                LIMIT %s OFFSET %s
            """, params + [per_page, offset])

            rows = cursor.fetchall()

            if not rows:
                return {
                    'orders': [],
                    'total': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                }

            orders = self._rows_to_dicts(cursor, rows)
            total = int(orders[0]['total_count']) if orders else 0
            total_pages = (total + per_page - 1) // per_page

            # Remove total_count from individual records
            for order in orders:
                del order['total_count']

            return {
                'orders': orders,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            }

    def update_order_item(
        self,
        order_item_id: int,
        updates: Dict,
        changed_by_user_id: int,
        reason: str = None
    ) -> bool:
        """
        Update order item with audit trail and optimistic locking.

        Args:
            order_item_id: ID of order item to update
            updates: Dictionary of fields to update (quantity, special_instructions, etc.)
            changed_by_user_id: User making the change
            reason: Reason for the change

        Returns:
            True if successful, raises exception on concurrency conflict
        """
        from src.repositories.audit_repository import AuditRepository
        audit_repo = AuditRepository()

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get old values for audit
                cursor.execute(
                    "SELECT * FROM kitch_order_item WHERE order_item_id = %s",
                    (order_item_id,)
                )
                old_row = cursor.fetchone()

                if not old_row:
                    raise ValueError(f"Order item {order_item_id} not found")

                old_values = dict(zip([desc[0] for desc in cursor.description], old_row))
                order_id = old_values['order_id']
                old_updated_at = old_values.get('updated_at')

                # Build update query
                set_clauses = []
                params = []

                for field, value in updates.items():
                    if field in ['quantity', 'special_instructions']:
                        set_clauses.append(f"{field} = %s")
                        params.append(value)

                if not set_clauses:
                    return False

                # Add updated_at for optimistic locking
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")

                # Update with optimistic lock check
                set_sql = ", ".join(set_clauses)
                params.extend([order_item_id, old_updated_at])

                cursor.execute(f"""
                    UPDATE kitch_order_item
                    SET {set_sql}
                    WHERE order_item_id = %s AND updated_at = %s
                    RETURNING *
                """, params)

                if cursor.rowcount == 0:
                    raise ValueError("Order item was modified by another user. Please refresh and try again.")

                new_row = cursor.fetchone()
                new_values = dict(zip([desc[0] for desc in cursor.description], new_row))

                # Recalculate order totals
                self._recalculate_order_totals(cursor, order_id)

                # Create audit record
                audit_repo.create_edit_record(
                    order_id=order_id,
                    entity_type='order_item',
                    entity_id=order_item_id,
                    action='update',
                    old_values={k: str(v) if isinstance(v, Decimal) else v for k, v in old_values.items()},
                    new_values={k: str(v) if isinstance(v, Decimal) else v for k, v in new_values.items()},
                    changed_by_user_id=changed_by_user_id,
                    reason=reason
                )

                conn.commit()
                return True

    def delete_order_item(
        self,
        order_item_id: int,
        changed_by_user_id: int,
        reason: str = None
    ) -> bool:
        """
        Delete order item with audit trail.
        Prevents deletion if it's the last item in the order.

        Args:
            order_item_id: ID of order item to delete
            changed_by_user_id: User making the change
            reason: Reason for deletion

        Returns:
            True if successful
        """
        from src.repositories.audit_repository import AuditRepository
        audit_repo = AuditRepository()

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get item details and check item count
                cursor.execute("""
                    SELECT oi.*,
                           (SELECT COUNT(*) FROM kitch_order_item WHERE order_id = oi.order_id) as item_count
                    FROM kitch_order_item oi
                    WHERE oi.order_item_id = %s
                """, (order_item_id,))

                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Order item {order_item_id} not found")

                old_values = dict(zip([desc[0] for desc in cursor.description], row))
                order_id = old_values['order_id']
                item_count = old_values['item_count']

                # Prevent deletion of last item
                if item_count <= 1:
                    raise ValueError("Cannot remove last item from order")

                # Create audit record before deletion
                audit_repo.create_edit_record(
                    order_id=order_id,
                    entity_type='order_item',
                    entity_id=order_item_id,
                    action='delete',
                    old_values={k: str(v) if isinstance(v, Decimal) else v for k, v in old_values.items()},
                    new_values={},
                    changed_by_user_id=changed_by_user_id,
                    reason=reason
                )

                # Delete item
                cursor.execute(
                    "DELETE FROM kitch_order_item WHERE order_item_id = %s",
                    (order_item_id,)
                )

                # Recalculate order totals
                self._recalculate_order_totals(cursor, order_id)

                conn.commit()
                return True

    def add_order_item(
        self,
        order_id: int,
        item_data: Dict,
        changed_by_user_id: int,
        reason: str = None
    ) -> Optional[int]:
        """
        Add new item to existing order with audit trail.

        Args:
            order_id: ID of order to add item to
            item_data: Dictionary with kic_id, quantity, unit_price, name, line_total, etc.
            changed_by_user_id: User making the change
            reason: Reason for adding item

        Returns:
            New order_item_id if successful
        """
        from src.repositories.audit_repository import AuditRepository
        audit_repo = AuditRepository()

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Verify order exists
                cursor.execute("SELECT 1 FROM kitch_order WHERE order_id = %s", (order_id,))
                if not cursor.fetchone():
                    raise ValueError(f"Order {order_id} not found")

                # Insert new item
                item_data['order_id'] = order_id
                item_fields = list(item_data.keys())
                placeholders = ', '.join(['%s'] * len(item_fields))
                fields_str = ', '.join(item_fields)

                cursor.execute(f"""
                    INSERT INTO kitch_order_item ({fields_str})
                    VALUES ({placeholders})
                    RETURNING *
                """, list(item_data.values()))

                new_row = cursor.fetchone()
                new_values = dict(zip([desc[0] for desc in cursor.description], new_row))
                order_item_id = new_values['order_item_id']

                # Recalculate order totals
                self._recalculate_order_totals(cursor, order_id)

                # Create audit record
                audit_repo.create_edit_record(
                    order_id=order_id,
                    entity_type='order_item',
                    entity_id=order_item_id,
                    action='add_item',
                    old_values={},
                    new_values={k: str(v) if isinstance(v, Decimal) else v for k, v in new_values.items()},
                    changed_by_user_id=changed_by_user_id,
                    reason=reason
                )

                conn.commit()
                return order_item_id

    def update_order_with_audit(
        self,
        order_id: int,
        updates: Dict,
        changed_by_user_id: int,
        reason: str = None
    ) -> bool:
        """
        Update order fields with audit trail.

        Args:
            order_id: Order ID
            updates: Dictionary of fields to update (discount_amount, discount_type, tip_amount, notes)
            changed_by_user_id: User making the change
            reason: Reason for change

        Returns:
            True if successful
        """
        from src.repositories.audit_repository import AuditRepository
        audit_repo = AuditRepository()

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get old values
                cursor.execute("SELECT * FROM kitch_order WHERE order_id = %s", (order_id,))
                old_row = cursor.fetchone()

                if not old_row:
                    raise ValueError(f"Order {order_id} not found")

                old_values = dict(zip([desc[0] for desc in cursor.description], old_row))

                # Build update query
                set_clauses = []
                params = []

                for field, value in updates.items():
                    if field in ['discount_amount', 'discount_type', 'tip_amount', 'notes']:
                        set_clauses.append(f"{field} = %s")
                        params.append(value)

                if not set_clauses:
                    return False

                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                set_sql = ", ".join(set_clauses)
                params.append(order_id)

                cursor.execute(f"""
                    UPDATE kitch_order
                    SET {set_sql}
                    WHERE order_id = %s
                    RETURNING *
                """, params)

                new_row = cursor.fetchone()
                new_values = dict(zip([desc[0] for desc in cursor.description], new_row))

                # Recalculate totals if discount or tip changed
                if any(field in updates for field in ['discount_amount', 'discount_type', 'tip_amount']):
                    self._recalculate_order_totals(cursor, order_id)

                # Create audit record
                audit_repo.create_edit_record(
                    order_id=order_id,
                    entity_type='order',
                    entity_id=order_id,
                    action='update',
                    old_values={k: str(v) if isinstance(v, Decimal) else v for k, v in old_values.items()},
                    new_values={k: str(v) if isinstance(v, Decimal) else v for k, v in new_values.items()},
                    changed_by_user_id=changed_by_user_id,
                    reason=reason
                )

                conn.commit()
                return True

    def bulk_update_status(
        self,
        order_ids: List[int],
        status_id: int,
        changed_by_user_id: int,
        note: str = None
    ) -> Dict:
        """
        Update status for multiple orders.

        Args:
            order_ids: List of order IDs to update
            status_id: New status ID
            changed_by_user_id: User making the change
            note: Optional note for status change

        Returns:
            Dictionary with success_count, failed_ids, and errors
        """
        success_count = 0
        failed_ids = []
        errors = {}

        for order_id in order_ids:
            try:
                success = self.update_order_status(
                    order_id=order_id,
                    status_id=status_id,
                    changed_by_user_id=changed_by_user_id,
                    note=note
                )
                if success:
                    success_count += 1
                else:
                    failed_ids.append(order_id)
                    errors[order_id] = "Update returned False"
            except Exception as e:
                failed_ids.append(order_id)
                errors[order_id] = str(e)

        return {
            'success_count': success_count,
            'failed_ids': failed_ids,
            'errors': errors
        }

    def _recalculate_order_totals(self, cursor, order_id: int):
        """
        Recalculate and update order totals after item changes.

        Args:
            cursor: Database cursor (must be within transaction)
            order_id: Order ID to recalculate
        """
        # Get current order data
        cursor.execute(
            "SELECT discount_amount, discount_type, tip_amount, tax_amount FROM kitch_order WHERE order_id = %s",
            (order_id,)
        )
        order_row = cursor.fetchone()
        if not order_row:
            return

        discount_amount = order_row[0] or Decimal('0')
        discount_type = order_row[1]
        tip_amount = order_row[2] or Decimal('0')
        tax_amount = order_row[3] or Decimal('0')

        # Calculate new subtotal from items
        cursor.execute(
            "SELECT SUM(line_total) FROM kitch_order_item WHERE order_id = %s",
            (order_id,)
        )
        subtotal = cursor.fetchone()[0] or Decimal('0')

        # Apply discount
        if discount_type == 'percent':
            discount_value = subtotal * (discount_amount / Decimal('100'))
        elif discount_type == 'fixed':
            discount_value = min(discount_amount, subtotal)
        else:
            discount_value = Decimal('0')

        # Calculate total
        total_amount = subtotal - discount_value + tip_amount + tax_amount

        # Update order
        cursor.execute("""
            UPDATE kitch_order
            SET subtotal = %s, total_amount = %s, updated_at = CURRENT_TIMESTAMP
            WHERE order_id = %s
        """, (subtotal, total_amount, order_id))
