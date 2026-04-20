"""Payment service for payment tracking."""
from decimal import Decimal
from typing import Tuple, Dict, Optional
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
                      recorded_by_user_id: int = None,
                      override_amount: float = None,
                      override_reason: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Record a manual payment with optional amount override (staff only).

        Args:
            order_id: Order ID
            amount: Payment amount
            payment_method: Payment method (cash, card, other)
            payment_status: Payment status
            tip_amount: Tip amount
            payment_notes: Optional notes
            recorded_by_user_id: User recording the payment
            override_amount: Optional override amount (staff can adjust final payment)
            override_reason: Reason for override (required if override_amount provided)

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

        # Validate override
        if override_amount is not None:
            if override_amount < 0:
                return False, "Override amount cannot be negative", None
            if not override_reason:
                return False, "Override reason is required when using override amount", None

        # Check if order exists
        order = self.order_repo.get_order_with_items(order_id)
        if not order:
            return False, "Order not found", None

        try:
            # Create payment record with override fields
            payment_data_dict = {
                'order_id': order_id,
                'amount': Decimal(str(amount)),
                'payment_method': payment_method,
                'payment_status': payment_status,
                'tip_amount': Decimal(str(tip_amount)),
                'payment_notes': payment_notes,
                'recorded_by_user_id': recorded_by_user_id
            }

            if override_amount is not None:
                payment_data_dict['override_amount'] = Decimal(str(override_amount))
                payment_data_dict['override_reason'] = override_reason
                payment_data_dict['override_by_user_id'] = recorded_by_user_id

            payment_id = self.payment_repo.create_payment(**payment_data_dict)

            if not payment_id:
                return False, "Failed to create payment record", None

            # Calculate total paid (considering override if present)
            total_paid = self.payment_repo.get_total_paid_for_order(order_id)

            # Use override amount for comparison if provided, otherwise use order total
            comparison_total = Decimal(str(override_amount)) if override_amount is not None else Decimal(str(order['total_amount']))

            # Update order payment status
            if total_paid >= comparison_total:
                new_payment_status = 'paid'
            elif total_paid > 0:
                new_payment_status = 'partially_paid'
            else:
                new_payment_status = 'pending'

            self.order_repo.update_payment_status(order_id, new_payment_status)

            # Check for auto-transition to Complete
            if new_payment_status == 'paid':
                self._check_auto_transition_to_complete(order_id, recorded_by_user_id)

            payment_data = {
                'payment_id': payment_id,
                'order_id': order_id,
                'amount': float(amount),
                'payment_method': payment_method,
                'payment_status': payment_status,
                'tip_amount': float(tip_amount),
                'override_amount': float(override_amount) if override_amount else None,
                'override_reason': override_reason,
                'order_payment_status': new_payment_status,
                'total_paid': float(total_paid)
            }

            return True, "Payment recorded successfully", payment_data

        except Exception as e:
            return False, f"Failed to record payment: {str(e)}", None

    def _check_auto_transition_to_complete(self, order_id: int, user_id: int):
        """
        Auto-transition Delivered → Complete when payment is marked as paid.

        Args:
            order_id: Order ID
            user_id: User ID for audit trail
        """
        try:
            # Get current order
            order = self.order_repo.find_by_id(order_id)
            if not order:
                return

            # Get statuses
            statuses = self.order_repo.get_all_statuses()
            status_map = {s['status_name']: s['status_id'] for s in statuses}

            delivered_status_id = status_map.get('Delivered')
            completed_status_id = status_map.get('Completed')

            # Only transition if current status is Delivered
            if order['current_status_id'] == delivered_status_id and completed_status_id:
                self.order_repo.update_order_status(
                    order_id=order_id,
                    status_id=completed_status_id,
                    changed_by_user_id=user_id,
                    note='Auto-completed: Payment received'
                )

        except Exception as e:
            # Log error but don't fail the payment recording
            print(f"Auto-transition failed for order {order_id}: {str(e)}")

    def refund_all_payments(self, order_id: int, user_id: int = None) -> Tuple[bool, str, Optional[Dict]]:
        """Mark all non-refunded payment records as refunded and set order payment_status to refunded."""
        order = self.order_repo.find_by_id(order_id)
        if not order:
            return False, "Order not found", None

        payments = self.payment_repo.get_payments_for_order(order_id)
        for payment in payments:
            if payment['payment_status'] != 'refunded':
                self.payment_repo.refund_payment(payment['payment_id'])

        self.order_repo.update_payment_status(order_id, 'refunded')
        return True, "Full refund issued successfully", None

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

    def refund_payment(self, order_id: int, payment_id: int,
                       refund_reason: str = None,
                       refunded_by_user_id: int = None) -> Tuple[bool, str, Optional[Dict]]:
        """Refund a specific payment record and recalculate order payment status."""
        payments = self.payment_repo.get_payments_for_order(order_id)
        payment = next((p for p in payments if p['payment_id'] == payment_id), None)

        if not payment:
            return False, "Payment not found for this order", None
        if payment['payment_status'] == 'refunded':
            return False, "Payment is already refunded", None

        success = self.payment_repo.refund_payment(payment_id)
        if not success:
            return False, "Failed to refund payment", None

        # Recalculate order payment status
        total_paid = self.payment_repo.get_total_paid_for_order(order_id)
        order = self.order_repo.find_by_id(order_id)

        if total_paid <= 0:
            new_status = 'refunded'
        elif total_paid < Decimal(str(order['total_amount'])):
            new_status = 'partially_paid'
        else:
            new_status = 'paid'

        self.order_repo.update_payment_status(order_id, new_status)
        return True, "Payment refunded successfully", {'order_payment_status': new_status}

    def update_order_payment_status(self, order_id: int, payment_status: str) -> Tuple[bool, str]:
        """Manually set the order-level payment status (staff override)."""
        valid_statuses = ['pending', 'paid', 'partially_paid', 'refunded']
        if payment_status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

        order = self.order_repo.find_by_id(order_id)
        if not order:
            return False, "Order not found"

        self.order_repo.update_payment_status(order_id, payment_status)
        return True, f"Payment status updated to {payment_status}"
