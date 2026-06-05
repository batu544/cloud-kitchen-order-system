"""Admin API — user management."""
from flask import Blueprint, request, g
from src.middleware.auth_middleware import require_auth
from src.repositories.user_repository import UserRepository
from src.utils.responses import success_response, error_response

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
user_repo = UserRepository()

ALLOWED_ROLES = {'customer', 'staff', 'admin'}


def _require_admin():
    user = g.current_user
    if not user or user.get('role') != 'admin':
        return error_response("Admin access required", 403)
    return None


@admin_bp.route('/users', methods=['GET'])
@require_auth
def list_users():
    err = _require_admin()
    if err:
        return err
    users = user_repo.get_all_users()
    # Strip password hashes before returning
    for u in users:
        u.pop('password_hash', None)
    return success_response(users)


@admin_bp.route('/users', methods=['POST'])
@require_auth
def create_user():
    err = _require_admin()
    if err:
        return err
    data = request.get_json() or {}

    # Required fields
    cust_name = data.get('cust_name')
    cust_phone_number = data.get('cust_phone_number')
    
    # Username is ALWAYS the phone number
    username = cust_phone_number
    # Optional fields
    email = data.get('email')

    if not all([cust_name, cust_phone_number]):
        return error_response("Missing required fields: cust_name, cust_phone_number", 400)

    from src.services.auth_service import AuthService
    auth_service = AuthService()

    # Use a default password that the user must change on first login
    DEFAULT_PASSWORD = "Password123!"

    success, message, user_data = auth_service.register_user(
        username=username,
        password=DEFAULT_PASSWORD,
        phone=cust_phone_number,
        cust_name=cust_name,
        email=email,
        requires_password_change=True
    )

    if not success:
        return error_response(message, 400)

    return success_response(user_data, "User created successfully with default password", 201)


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_auth
def update_user(user_id):
    err = _require_admin()
    if err:
        return err
    data = request.get_json() or {}
    updates = {}
    if 'role' in data:
        if data['role'] not in ALLOWED_ROLES:
            return error_response("Invalid role", 400)
        updates['role'] = data['role']
    if 'is_active' in data:
        updates['is_active'] = bool(data['is_active'])
    if not updates:
        return error_response("No valid fields to update", 400)
    ok = user_repo.update_user(user_id, updates)
    if not ok:
        return error_response("User not found", 404)
    return success_response({'user_id': user_id, **updates})


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_auth
def delete_user(user_id):
    err = _require_admin()
    if err:
        return err
    # Prevent self-deletion
    if g.current_user.get('user_id') == user_id:
        return error_response("Cannot delete your own account", 400)
    ok = user_repo.delete_user(user_id)
    if not ok:
        return error_response("User not found", 404)
    return success_response({'deleted': user_id})
