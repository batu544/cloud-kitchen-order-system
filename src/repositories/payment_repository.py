"""Payment repository."""
from typing import Optional, Dict, List
from decimal import Decimal
from src.repositories.base import BaseRepository
from src.database.connection import get_db_cursor


class PaymentRepository(BaseRepository):
    """Repository for payment operations."""

    def __init__(self):
        super().__init__('kitch_payment', 'payment_id')

    def create_payment(self, order_id: int, amount: Decimal, payment_method: str,
                      payment_status: str, tip_amount: Decimal = Decimal('0'),
                      payment_notes: str = None, recorded_by_user_id: int = None,
                      override_amount: Decimal = None, override_reason: str = None,
                      override_by_user_id: int = None) -> Optional[int]:
        """
        Create a payment record with optional override fields.

        Args:
            order_id: Order ID
            amount: Payment amount
            payment_method: Payment method (cash, card, other)
            payment_status: Payment status
            tip_amount: Tip amount
            payment_notes: Optional notes
            recorded_by_user_id: User recording the payment
            override_amount: Optional override amount for final payment adjustment
            override_reason: Reason for override (required if override_amount provided)
            override_by_user_id: User who authorized the override

        Returns:
            New payment ID or None
        """
        data = {
            'order_id': order_id,
            'amount': amount,
            'payment_method': payment_method,
            'payment_status': payment_status,
            'tip_amount': tip_amount,
            'payment_notes': payment_notes,
            'recorded_by_user_id': recorded_by_user_id,
            'override_amount': override_amount,
            'override_reason': override_reason,
            'override_by_user_id': override_by_user_id
        }
        return self.insert(data)

    def get_payments_for_order(self, order_id: int) -> List[Dict]:
        """
        Get all payments for an order.

        Args:
            order_id: Order ID

        Returns:
            List of payment dictionaries
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT * FROM kitch_payment
                WHERE order_id = %s
                ORDER BY payment_date DESC
                """,
                (order_id,)
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)

    def get_total_paid_for_order(self, order_id: int) -> Decimal:
        """
        Calculate total amount paid for an order.

        Args:
            order_id: Order ID

        Returns:
            Total amount paid
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount), 0) as total_paid
                FROM kitch_payment
                WHERE order_id = %s AND payment_status IN ('paid', 'partially_paid')
                """,
                (order_id,)
            )
            result = cursor.fetchone()
            return Decimal(result[0]) if result else Decimal('0')

    def refund_payment(self, payment_id: int) -> bool:
        """Mark a specific payment record as refunded."""
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE kitch_payment SET payment_status = 'refunded' WHERE payment_id = %s",
                (payment_id,)
            )
            return cursor.rowcount > 0
