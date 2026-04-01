"""Repository for order edit audit trail operations."""
import json
import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from src.repositories.base import BaseRepository
from src.database.connection import get_db_connection


class _AuditJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class AuditRepository(BaseRepository):
    """Repository for tracking order and order item edits."""

    def __init__(self):
        """Initialize with kitch_order_edit_history table."""
        super().__init__('kitch_order_edit_history', 'edit_id')

    def create_edit_record(
        self,
        order_id: int,
        entity_type: str,
        entity_id: int,
        action: str,
        old_values: Dict,
        new_values: Dict,
        changed_by_user_id: int,
        reason: Optional[str] = None
    ) -> Optional[int]:
        """
        Create an audit trail record for an order or order item edit.

        Args:
            order_id: ID of the order being modified
            entity_type: 'order' or 'order_item'
            entity_id: ID of the specific entity (order_id or order_item_id)
            action: 'update', 'delete', or 'add_item'
            old_values: Dictionary of field values before change
            new_values: Dictionary of field values after change
            changed_by_user_id: ID of user making the change
            reason: Optional reason for the change

        Returns:
            edit_id if successful, None otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO kitch_order_edit_history (
                        order_id,
                        entity_type,
                        entity_id,
                        action,
                        old_values,
                        new_values,
                        changed_by_user_id,
                        change_reason
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING edit_id
                """, (
                    order_id,
                    entity_type,
                    entity_id,
                    action,
                    json.dumps(old_values, cls=_AuditJSONEncoder),
                    json.dumps(new_values, cls=_AuditJSONEncoder),
                    changed_by_user_id,
                    reason
                ))

                edit_id = cursor.fetchone()[0]
                return edit_id
            finally:
                cursor.close()

    def get_order_edits(
        self,
        order_id: int,
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get edit history for an order.

        Args:
            order_id: ID of the order
            entity_type: Optional filter for 'order' or 'order_item' edits
            limit: Maximum number of records to return (default 100)

        Returns:
            List of edit records with user information
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                where_clause = "WHERE oeh.order_id = %s"
                params = [order_id]

                if entity_type:
                    where_clause += " AND oeh.entity_type = %s"
                    params.append(entity_type)

                params.append(limit)

                cursor.execute(f"""
                    SELECT
                        oeh.edit_id,
                        oeh.order_id,
                        oeh.entity_type,
                        oeh.entity_id,
                        oeh.action,
                        oeh.old_values,
                        oeh.new_values,
                        oeh.change_reason,
                        oeh.changed_at,
                        oeh.changed_by_user_id,
                        u.username as changed_by_username,
                        u.role as changed_by_role
                    FROM kitch_order_edit_history oeh
                    LEFT JOIN kitch_user u ON oeh.changed_by_user_id = u.user_id
                    {where_clause}
                    ORDER BY oeh.changed_at DESC
                    LIMIT %s
                """, params)

                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    record = dict(zip(columns, row))
                    results.append(record)

                return results
            finally:
                cursor.close()

    def get_edit_count_by_order(self, order_id: int) -> int:
        """
        Get total number of edits for an order.

        Args:
            order_id: ID of the order

        Returns:
            Number of edit records
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM kitch_order_edit_history
                    WHERE order_id = %s
                """, (order_id,))

                count = cursor.fetchone()[0]
                return count
            finally:
                cursor.close()

    def get_recent_edits(
        self,
        hours: int = 24,
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get recent edits across all orders.

        Args:
            hours: Number of hours to look back (default 24)
            entity_type: Optional filter for 'order' or 'order_item'
            limit: Maximum number of records (default 100)

        Returns:
            List of recent edit records with order and user information
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                where_clause = "WHERE oeh.changed_at >= NOW() - INTERVAL '%s hours'"
                params = [hours]

                if entity_type:
                    where_clause += " AND oeh.entity_type = %s"
                    params.append(entity_type)

                params.append(limit)

                cursor.execute(f"""
                    SELECT
                        oeh.edit_id,
                        oeh.order_id,
                        o.order_ref,
                        oeh.entity_type,
                        oeh.entity_id,
                        oeh.action,
                        oeh.old_values,
                        oeh.new_values,
                        oeh.change_reason,
                        oeh.changed_at,
                        u.username as changed_by_username,
                        u.role as changed_by_role
                    FROM kitch_order_edit_history oeh
                    LEFT JOIN kitch_order o ON oeh.order_id = o.order_id
                    LEFT JOIN kitch_user u ON oeh.changed_by_user_id = u.user_id
                    {where_clause}
                    ORDER BY oeh.changed_at DESC
                    LIMIT %s
                """, params)

                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                results = []
                for row in rows:
                    record = dict(zip(columns, row))
                    results.append(record)

                return results
            finally:
                cursor.close()
