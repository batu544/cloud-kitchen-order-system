"""Authentication middleware for JWT verification and role-based access."""
from functools import wraps
from flask import request, g
from src.utils.security import decode_jwt_token, extract_token_from_header
from src.utils.responses import unauthorized_response, forbidden_response


def require_auth(f):
    """
    Decorator for protected routes requiring authentication.

    Usage:
        @require_auth
        def protected_route():
            user = g.current_user  # Access authenticated user
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        token = extract_token_from_header(auth_header)

        if not token:
            return unauthorized_response("Missing authorization token")

        # Decode and verify token
        payload = decode_jwt_token(token)

        if not payload:
            return unauthorized_response("Invalid or expired token")

        # Store user info in Flask g object for access in route
        g.current_user = payload

        return f(*args, **kwargs)

    return decorated_function


def require_role(*allowed_roles):
    """
    Decorator for role-based access control.

    Must be used AFTER @require_auth decorator.

    Usage:
        @require_auth
        @require_role('staff', 'admin')
        def staff_only_route():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return unauthorized_response("Authentication required")

            user_role = g.current_user.get('role')

            if user_role not in allowed_roles:
                return forbidden_response("Insufficient permissions")

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def optional_auth(f):
    """
    Decorator for routes that work with or without authentication.

    If token is present and valid, sets g.current_user.
    If token is missing or invalid, continues without authentication.

    Usage:
        @optional_auth
        def public_or_authenticated_route():
            if hasattr(g, 'current_user'):
                # User is authenticated
                pass
            else:
                # User is not authenticated
                pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try to extract token
        auth_header = request.headers.get('Authorization')
        token = extract_token_from_header(auth_header)

        if token:
            # Try to decode token
            payload = decode_jwt_token(token)
            if payload:
                g.current_user = payload

        return f(*args, **kwargs)

    return decorated_function
