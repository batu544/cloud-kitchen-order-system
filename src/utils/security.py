"""Security utilities for password hashing and JWT tokens."""
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from config import Config


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password to verify
        password_hash: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def generate_jwt_token(user_id: int, username: str, role: str, cust_id: int = None) -> str:
    """
    Generate a JWT token for a user.

    Args:
        user_id: User's database ID
        username: User's username
        role: User's role (customer, staff, admin)
        cust_id: Optional linked customer ID

    Returns:
        JWT token string
    """
    expiration = datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRATION_HOURS)

    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': expiration,
        'iat': datetime.now(timezone.utc)
    }
    if cust_id is not None:
        payload['cust_id'] = cust_id

    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
    return token


def decode_jwt_token(token: str) -> Optional[Dict]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dictionary if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def extract_token_from_header(auth_header: Optional[str]) -> Optional[str]:
    """
    Extract JWT token from Authorization header.

    Args:
        auth_header: Authorization header value (e.g., "Bearer <token>")

    Returns:
        Token string if valid format, None otherwise
    """
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    return parts[1]
