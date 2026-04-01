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


@orders_bp.route('/track/<int:order_id>', methods=['GET'])
def track_order(order_id):
    """
    Public order tracking by order ID.

    Args:
        order_id: Order ID (numeric)

    Returns:
        200: Order details with status history
        404: Order not found
    """
    success, message, order_data = order_service.track_order(order_id)

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


@orders_bp.route('/daily', methods=['GET'])
@require_auth
@require_role('staff', 'admin')
def get_daily_orders():
    """
    Get orders for a specific day with pagination (staff dashboard).

    Headers:
        Authorization: Bearer <token>

    Query parameters:
        date: ISO date (YYYY-MM-DD), defaults to today
        page: Page number (default 1)
        per_page: Items per page (default 10, max 50)
        status: Optional status_id filter

    Returns:
        200: Orders with pagination info
        403: Forbidden (not staff)
    """
    date = request.args.get('date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status_filter = request.args.get('status', type=int)

    success, message, data = order_service.get_daily_orders(
        date=date,
        page=page,
        per_page=per_page,
        status_filter=status_filter
    )

    if success:
        return success_response(data, message)
    else:
        return error_response(message, 400)


@orders_bp.route('/<int:order_id>/items/<int:order_item_id>', methods=['PUT'])
@require_auth
@require_role('staff', 'admin')
def edit_order_item(order_id, order_item_id):
    """
    Edit order item (quantity, special instructions).

    Headers:
        Authorization: Bearer <token>

    Request body:
        {
            "quantity": 3,  // optional
            "special_instructions": "No onions",  // optional
            "reason": "Customer requested change"  // optional
        }

    Returns:
        200: Order item updated successfully
        400: Validation error or order completed/cancelled
        403: Forbidden (not staff)
        404: Order item not found
        409: Concurrency conflict
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    updates = {}
    if 'quantity' in data:
        updates['quantity'] = data['quantity']
    if 'special_instructions' in data:
        updates['special_instructions'] = data['special_instructions']

    reason = data.get('reason')
    changed_by_user_id = g.current_user.get('user_id')

    success, message, updated_order = order_service.edit_order_item(
        order_item_id=order_item_id,
        updates=updates,
        changed_by_user_id=changed_by_user_id,
        reason=reason
    )

    if success:
        return success_response(updated_order, message)
    else:
        # Determine status code based on error message
        if "not found" in message.lower():
            status_code = 404
        elif "modified by another user" in message.lower():
            status_code = 409
        else:
            status_code = 400
        return error_response(message, status_code)


@orders_bp.route('/<int:order_id>/items/<int:order_item_id>', methods=['DELETE'])
@require_auth
@require_role('staff', 'admin')
def remove_order_item(order_id, order_item_id):
    """
    Remove item from order.

    Headers:
        Authorization: Bearer <token>

    Request body:
        {
            "reason": "Customer no longer wants this item"  // optional
        }

    Returns:
        200: Item removed successfully
        400: Validation error (e.g., last item, order completed)
        403: Forbidden (not staff)
        404: Order item not found
    """
    data = request.get_json() or {}
    reason = data.get('reason')
    changed_by_user_id = g.current_user.get('user_id')

    success, message, updated_order = order_service.remove_order_item(
        order_item_id=order_item_id,
        changed_by_user_id=changed_by_user_id,
        reason=reason
    )

    if success:
        return success_response(updated_order, message)
    else:
        status_code = 404 if "not found" in message.lower() else 400
        return error_response(message, status_code)


@orders_bp.route('/<int:order_id>/items', methods=['POST'])
@require_auth
@require_role('staff', 'admin')
def add_order_item(order_id):
    """
    Add new item to existing order.

    Headers:
        Authorization: Bearer <token>

    Request body:
        {
            "kic_id": 5,
            "quantity": 2,
            "special_instructions": "Extra spicy",  // optional
            "is_catering": false,  // optional
            "catering_size": null,  // optional: "small", "medium", "large"
            "reason": "Customer added item"  // optional
        }

    Returns:
        200: Item added successfully
        400: Validation error
        403: Forbidden (not staff)
        404: Order or menu item not found
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    item_data = {
        'kic_id': data.get('kic_id'),
        'quantity': data.get('quantity', 1),
        'special_instructions': data.get('special_instructions'),
        'is_catering': data.get('is_catering', False),
        'catering_size': data.get('catering_size')
    }

    reason = data.get('reason')
    changed_by_user_id = g.current_user.get('user_id')

    success, message, updated_order = order_service.add_item_to_order(
        order_id=order_id,
        item_data=item_data,
        changed_by_user_id=changed_by_user_id,
        reason=reason
    )

    if success:
        return success_response(updated_order, message)
    else:
        status_code = 404 if "not found" in message.lower() else 400
        return error_response(message, status_code)


@orders_bp.route('/<int:order_id>', methods=['PUT'])
@require_auth
@require_role('staff', 'admin')
def update_order(order_id):
    """
    Update order-level fields (discount, tip, notes).

    Headers:
        Authorization: Bearer <token>

    Request body:
        {
            "discount": {  // optional
                "type": "percent",
                "value": 15
            },
            "tip_amount": 10.00,  // optional
            "notes": "Updated notes",  // optional
            "reason": "Staff adjustment"  // optional
        }

    Returns:
        200: Order updated successfully
        400: Validation error
        403: Forbidden (not staff)
        404: Order not found
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    updates = {}
    if 'discount' in data:
        updates['discount'] = data['discount']
    if 'tip_amount' in data:
        updates['tip_amount'] = data['tip_amount']
    if 'notes' in data:
        updates['notes'] = data['notes']

    reason = data.get('reason')
    changed_by_user_id = g.current_user.get('user_id')

    success, message, updated_order = order_service.update_order_metadata(
        order_id=order_id,
        updates=updates,
        changed_by_user_id=changed_by_user_id,
        reason=reason
    )

    if success:
        return success_response(updated_order, message)
    else:
        status_code = 404 if "not found" in message.lower() else 400
        return error_response(message, status_code)


@orders_bp.route('/bulk-status', methods=['PUT'])
@require_auth
@require_role('staff', 'admin')
def bulk_update_status():
    """
    Update status for multiple orders (bulk operation).

    Headers:
        Authorization: Bearer <token>

    Request body:
        {
            "order_ids": [123, 124, 125],
            "status_id": 3,
            "note": "Bulk update to Preparing"  // optional
        }

    Returns:
        200: Bulk update results (includes success_count, failed_ids, errors)
        400: Validation error
        403: Forbidden (not staff)
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    order_ids = data.get('order_ids', [])
    status_id = data.get('status_id')
    note = data.get('note')

    if not order_ids or not isinstance(order_ids, list):
        return error_response("order_ids must be a non-empty array", 400)

    if not status_id:
        return error_response("status_id is required", 400)

    changed_by_user_id = g.current_user.get('user_id')

    success, message, results = order_service.bulk_update_order_status(
        order_ids=order_ids,
        status_id=status_id,
        changed_by_user_id=changed_by_user_id,
        note=note
    )

    if success:
        return success_response(results, message)
    else:
        return error_response(message, 400)


@orders_bp.route('/<int:order_id>/history', methods=['GET'])
@require_auth
@require_role('staff', 'admin')
def get_order_history(order_id):
    """
    Get complete edit history for an order.

    Headers:
        Authorization: Bearer <token>

    Query parameters:
        entity_type: Optional filter for 'order' or 'order_item' edits

    Returns:
        200: List of edit history records
        403: Forbidden (not staff)
        404: Order not found
    """
    from src.repositories.audit_repository import AuditRepository
    audit_repo = AuditRepository()

    entity_type = request.args.get('entity_type')

    # Verify order exists
    order = order_service.order_repo.find_by_id(order_id)
    if not order:
        return error_response("Order not found", 404)

    # Get edit history
    edits = audit_repo.get_order_edits(order_id, entity_type=entity_type)

    return success_response(edits)
