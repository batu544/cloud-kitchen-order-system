"""Payment service for payment tracking."""
from decimal import Decimal
from typing import Tuple, List, Dict, Optional
from src.repositories.payment_repository import PaymentRepository
from src.repositories.order_repository import OrderRepository
from src.utils.validators import validate_payment_method, validate_payment_status


class PaymentService:
    """Service for payment operations."""

    def __init__(self):
        self.payment_repo = PaymentRepository()
        self.order_repo = OrderRepository()

    def record_payment(self, order_id: int, amount: float, payment_method: str,
                      payment_status: str, tip_amount: float = 0,
                      payment_notes: str = None,
                      recorded_by_user_id: int = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Record a manual payment (staff only).

        Args:
            order_id: Order ID
            amount: Payment amount
            payment_method: Payment method (cash, card, other)
            payment_status: Payment status
            tip_amount: Tip amount
            payment_notes: Optional notes
            recorded_by_user_id: User recording the payment

        Returns:
            Tuple of (success, message, payment_data)
        """
        # Validate payment method
        is_valid_method, method_error = validate_payment_method(payment_method)
        if not is_valid_method:
            return False, method_error, None

        # Validate payment status
        is_valid_status, status_error = validate_payment_status(payment_status)
        if not is_valid_status:
            return False, status_error, None

        # Check if order exists
        order = self.order_repo.get_order_with_items(order_id)
        if not order:
            return False, "Order not found", None

        try:
            # Create payment record
            payment_id = self.payment_repo.create_payment(
                order_id=order_id,
                amount=Decimal(str(amount)),
                payment_method=payment_method,
                payment_status=payment_status,
                tip_amount=Decimal(str(tip_amount)),
                payment_notes=payment_notes,
                recorded_by_user_id=recorded_by_user_id
            )

            if not payment_id:
                return False, "Failed to create payment record", None

            # Calculate total paid
            total_paid = self.payment_repo.get_total_paid_for_order(order_id)
            order_total = Decimal(str(order['total_amount']))

            # Update order payment status
            if total_paid >= order_total:
                new_payment_status = 'paid'
            elif total_paid > 0:
                new_payment_status = 'partially_paid'
            else:
                new_payment_status = 'pending'

            self.order_repo.update_payment_status(order_id, new_payment_status)

            payment_data = {
                'payment_id': payment_id,
                'order_id': order_id,
                'amount': float(amount),
                'payment_method': payment_method,
                'payment_status': payment_status,
                'tip_amount': float(tip_amount),
                'order_payment_status': new_payment_status,
                'total_paid': float(total_paid)
            }

            return True, "Payment recorded successfully", payment_data

        except Exception as e:
            return False, f"Failed to record payment: {str(e)}", None

    def get_order_payments(self, order_id: int) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get all payments for an order.

        Args:
            order_id: Order ID

        Returns:
            Tuple of (success, message, payments_data)
        """
        payments = self.payment_repo.get_payments_for_order(order_id)
        total_paid = self.payment_repo.get_total_paid_for_order(order_id)

        payments_data = {
            'payments': payments,
            'total_paid': float(total_paid)
        }

        return True, "Payments retrieved", payments_data
