"""Order API endpoints - Most complex endpoints."""
from flask import Blueprint, request, g
from src.services.order_service import OrderService
from src.middleware.auth_middleware import require_auth, require_role, optional_auth
from src.utils.responses import success_response, error_response

orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')
order_service = OrderService()


@orders_bp.route('', methods=['POST'])
@optional_auth
def create_order():
    """
    Create new order (guest, registered user, or staff).

    Headers:
        Authorization: Bearer <token> (optional for guest, required for staff)

    Request body:
        {
            "customer": {
                "cust_id": 1,  // optional, for existing customers
                "phone": "1234567890",  // required
                "name": "John Doe",  // optional for guests
                "email": "optional",
                "address": "optional"
            },
            "items": [
                {
                    "kic_id": 1,
                    "quantity": 2,
                    "special_instructions": "optional",
                    "is_catering": false,
                    "catering_size": null  // "small", "medium", "large" if catering
                }
            ],
            "discount": {  // optional, staff only
                "type": "percent",  // or "fixed"
                "value": 10
            },
            "tip_amount": 5.00,  // optional
            "notes": "optional order notes"
        }

    Returns:
        201: Order created successfully
        400: Validation error
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    # Get user ID if authenticated
    placed_by_user_id = None
    if hasattr(g, 'current_user'):
        placed_by_user_id = g.current_user.get('user_id')

    # Create order
    success, message, order_data = order_service.create_order(
        order_request=data,
        placed_by_user_id=placed_by_user_id
    )

    if success:
        return success_response(order_data, message, 201)
    else:
        return error_response(message, 400)


@orders_bp.route('/phone-lookup', methods=['POST'])
@require_auth
@require_role('staff', 'admin')
def phone_lookup():
    """
    Find customer by phone number (staff only) - SPEC.md line 26.

    Headers:
        Authorization: Bearer <token>

    Request body:
        {
            "phone": "1234567890"
        }

    Returns:
        200: Customer found with order history
        404: Customer not found
        403: Forbidden (not staff)
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    phone = data.get('phone')

    if not phone:
        return error_response("Phone number is required", 400)

    found, message, customer_data = order_service.lookup_customer_by_phone(phone)

    if found:
        return success_response(customer_data, message)
    else:
        return error_response(message, 404)


@orders_bp.route('/<int:order_id>', methods=['GET'])
@optional_auth
def get_order(order_id):
    """
    Get order details.

    Headers:
        Authorization: Bearer <token> (optional)

    Args:
        order_id: Order ID

    Returns:
        200: Order details
        401: Unauthorized (for orders belonging to other users)
        404: Order not found
    """
    user_id = None
    user_role = None

    if hasattr(g, 'current_user'):
        user_id = g.current_user.get('user_id')
        user_role = g.current_user.get('role')

    success, message, order_data = order_service.get_order(
        order_id=order_id,
        user_id=user_id,
        user_role=user_role
    )

    if success:
        return success_response(order_data, message)
    else:
        status_code = 401 if message == "Unauthorized" else 404
        return error_response(message, status_code)


@orders_bp.route('/track/<order_ref>', methods=['GET'])
def track_order(order_ref):
    """
    Public order tracking by order reference.

    Args:
        order_ref: Order reference string (e.g., ORD-20240328-ABC123)

    Returns:
        200: Order details with status history
        404: Order not found
    """
    success, message, order_data = order_service.track_order(order_ref)

    if success:
        return success_response(order_data, message)
    else:
        return error_response(message, 404)


@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@require_auth
@require_role('staff', 'admin')
def update_order_status(order_id):
    """
    Update order status (staff only).

    Headers:
        Authorization: Bearer <token>

    Args:
        order_id: Order ID

    Request body:
        {
            "status_id": 2,
            "note": "Optional status change note"
        }

    Returns:
        200: Status updated
        400: Validation error
        403: Forbidden (not staff)
        404: Order not found
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    status_id = data.get('status_id')
    note = data.get('note')

    if not status_id:
        return error_response("status_id is required", 400)

    changed_by_user_id = g.current_user.get('user_id')

    success, message = order_service.update_order_status(
        order_id=order_id,
        status_id=status_id,
        changed_by_user_id=changed_by_user_id,
        note=note
    )

    if success:
        return success_response(None, message)
    else:
        return error_response(message, 400)


@orders_bp.route('/my-orders', methods=['GET'])
@require_auth
def get_my_orders():
    """
    Get orders for authenticated user.

    Headers:
        Authorization: Bearer <token>

    Returns:
        200: List of user's orders
        401: Unauthorized
    """
    user = g.current_user
    cust_id = user.get('cust_id')

    if not cust_id:
        return success_response([])

    orders = order_service.get_customer_orders(cust_id)

    return success_response(orders)


@orders_bp.route('/recent', methods=['GET'])
@require_auth
@require_role('staff', 'admin')
def get_recent_orders():
    """
    Get recent orders (staff/admin only).

    Headers:
        Authorization: Bearer <token>

    Query parameters:
        limit: Maximum orders to return (default 50)

    Returns:
        200: List of recent orders
        403: Forbidden (not staff)
    """
    limit = request.args.get('limit', 50, type=int)

    orders = order_service.get_recent_orders(limit=limit)

    return success_response(orders)
