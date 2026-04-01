"""Payment API endpoints."""
from flask import Blueprint, request, g
from src.services.payment_service import PaymentService
from src.middleware.auth_middleware import require_auth, require_role
from src.utils.responses import success_response, error_response

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')
payment_service = PaymentService()


@payments_bp.route('/orders/<int:order_id>/payments', methods=['POST'])
@require_auth
@require_role('staff', 'admin')
def record_payment(order_id):
    """
    Record a manual payment with optional override (staff only).

    Headers:
        Authorization: Bearer <token>

    Args:
        order_id: Order ID

    Request body:
        {
            "amount": 50.00,
            "payment_method": "cash",  // "cash", "card", "other"
            "payment_status": "paid",  // "paid", "partially_paid"
            "tip_amount": 5.00,  // optional
            "payment_notes": "optional notes",
            "override_amount": 45.00,  // optional - staff can adjust final payment
            "override_reason": "Customer discount applied"  // required if override_amount provided
        }

    Returns:
        201: Payment recorded successfully (auto-transitions Delivered→Complete if paid)
        400: Validation error
        403: Forbidden (not staff)
        404: Order not found
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    amount = data.get('amount')
    payment_method = data.get('payment_method')
    payment_status = data.get('payment_status', 'paid')
    tip_amount = data.get('tip_amount', 0)
    payment_notes = data.get('payment_notes')
    override_amount = data.get('override_amount')
    override_reason = data.get('override_reason')

    # Validate required fields
    if amount is None or not payment_method:
        return error_response("amount and payment_method are required", 400)

    recorded_by_user_id = g.current_user.get('user_id')

    success, message, payment_data = payment_service.record_payment(
        order_id=order_id,
        amount=float(amount),
        payment_method=payment_method,
        payment_status=payment_status,
        tip_amount=float(tip_amount),
        payment_notes=payment_notes,
        recorded_by_user_id=recorded_by_user_id,
        override_amount=float(override_amount) if override_amount is not None else None,
        override_reason=override_reason
    )

    if success:
        return success_response(payment_data, message, 201)
    else:
        return error_response(message, 400)


@payments_bp.route('/orders/<int:order_id>/payments', methods=['GET'])
@require_auth
def get_order_payments(order_id):
    """
    Get all payments for an order.

    Headers:
        Authorization: Bearer <token>

    Args:
        order_id: Order ID

    Returns:
        200: Payment history
        401: Unauthorized
        404: Order not found
    """
    success, message, payments_data = payment_service.get_order_payments(order_id)

    if success:
        return success_response(payments_data, message)
    else:
        return error_response(message, 404)
