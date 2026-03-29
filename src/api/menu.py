"""Menu API endpoints."""
from flask import Blueprint, request
from src.services.menu_service import MenuService
from src.middleware.auth_middleware import require_auth, require_role
from src.utils.responses import success_response, error_response

menu_bp = Blueprint('menu', __name__, url_prefix='/api/menu')
menu_service = MenuService()


@menu_bp.route('', methods=['GET'])
def get_menu():
    """
    Get full menu with categories and items.

    Query parameters:
        category_id: Optional category filter
        is_catering: Optional catering items filter (true/false)

    Returns:
        200: Menu data with categories and items
    """
    category_id = request.args.get('category_id', type=int)
    is_catering = request.args.get('is_catering')

    # Convert is_catering to boolean
    if is_catering is not None:
        is_catering = is_catering.lower() in ['true', '1', 'yes']

    menu_data = menu_service.get_full_menu(
        category_id=category_id,
        is_catering=is_catering
    )

    return success_response(menu_data)


@menu_bp.route('/items/<int:kic_id>', methods=['GET'])
def get_item(kic_id):
    """
    Get specific menu item by ID.

    Args:
        kic_id: Menu item ID

    Returns:
        200: Item data
        404: Item not found
    """
    item = menu_service.get_item(kic_id)

    if item:
        return success_response(item)
    else:
        return error_response("Menu item not found", 404)


@menu_bp.route('/items', methods=['POST'])
@require_auth
@require_role('admin')
def create_item():
    """
    Create new menu item (admin only).

    Headers:
        Authorization: Bearer <token>

    Request body:
        {
            "name": "Item Name",
            "price": 12.99,
            "category_id": 1,
            "description": "Optional description",
            "is_catering": false,
            "image_url": "optional_url"
        }

    Returns:
        201: Item created
        400: Validation error
        403: Forbidden (not admin)
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    name = data.get('name')
    price = data.get('price')
    category_id = data.get('category_id')
    description = data.get('description')
    is_catering = data.get('is_catering', False)
    image_url = data.get('image_url')

    # Validate required fields
    if not all([name, price is not None, category_id]):
        return error_response("Missing required fields: name, price, category_id", 400)

    success, message, item_id = menu_service.create_item(
        name=name,
        price=float(price),
        category_id=category_id,
        description=description,
        is_catering=is_catering,
        image_url=image_url
    )

    if success:
        return success_response({'kic_id': item_id}, message, 201)
    else:
        return error_response(message, 400)


@menu_bp.route('/items/<int:kic_id>', methods=['PUT'])
@require_auth
@require_role('admin')
def update_item(kic_id):
    """
    Update menu item (admin only).

    Headers:
        Authorization: Bearer <token>

    Args:
        kic_id: Menu item ID

    Request body:
        {
            "name": "New Name",
            "price": 15.99,
            "description": "New description",
            "is_active": true,
            ...
        }

    Returns:
        200: Item updated
        400: Validation error
        403: Forbidden (not admin)
        404: Item not found
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    # Convert price to float if provided
    if 'price' in data and data['price'] is not None:
        data['price'] = float(data['price'])

    success, message = menu_service.update_item(kic_id, **data)

    if success:
        return success_response(None, message)
    else:
        return error_response(message, 400)
