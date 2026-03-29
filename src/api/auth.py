"""Authentication API endpoints."""
from flask import Blueprint, request, g
from src.services.auth_service import AuthService
from src.middleware.auth_middleware import require_auth
from src.utils.responses import success_response, error_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
auth_service = AuthService()


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account.

    Request body:
        {
            "username": "user@example.com",
            "password": "password123",
            "phone": "1234567890",
            "cust_name": "John Doe",
            "email": "optional@example.com",
            "address": "Optional address"
        }

    Returns:
        201: User registered successfully with token
        400: Validation error
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone')
    cust_name = data.get('cust_name')
    email = data.get('email')
    address = data.get('address')

    # Validate required fields
    if not all([username, password, phone, cust_name]):
        return error_response("Missing required fields: username, password, phone, cust_name", 400)

    # Register user
    success, message, user_data = auth_service.register_user(
        username=username,
        password=password,
        phone=phone,
        cust_name=cust_name,
        email=email,
        address=address
    )

    if success:
        return success_response(user_data, message, 201)
    else:
        return error_response(message, 400)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login and get JWT token.

    Request body:
        {
            "username": "user@example.com",
            "password": "password123"
        }

    Returns:
        200: Login successful with token
        401: Invalid credentials
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return error_response("Username and password are required", 400)

    # Authenticate
    success, message, user_data = auth_service.login(username, password)

    if success:
        return success_response(user_data, message)
    else:
        return error_response(message, 401)


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """
    Get current authenticated user information.

    Headers:
        Authorization: Bearer <token>

    Returns:
        200: User information
        401: Unauthorized
    """
    user_id = g.current_user.get('user_id')

    user_info = auth_service.get_user_info(user_id)

    if user_info:
        # Remove sensitive data
        user_info.pop('password_hash', None)
        return success_response(user_info)
    else:
        return error_response("User not found", 404)


@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """
    Change user password.

    Headers:
        Authorization: Bearer <token>

    Request body:
        {
            "current_password": "old_password",
            "new_password": "new_password"
        }

    Returns:
        200: Password changed successfully
        400: Invalid current password
        401: Unauthorized
    """
    data = request.get_json()

    if not data:
        return error_response("Request body is required", 400)

    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return error_response("Current password and new password are required", 400)

    user_id = g.current_user.get('user_id')

    success, message = auth_service.change_password(
        user_id, current_password, new_password
    )

    if success:
        return success_response(None, message)
    else:
        return error_response(message, 400)
