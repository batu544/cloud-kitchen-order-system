"""Standardized API response utilities."""
from typing import Any, Optional, Dict
from flask import jsonify


def success_response(data: Any = None, message: str = "Success", status_code: int = 200):
    """
    Create a standardized success response.

    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code

    Returns:
        Flask JSON response
    """
    response = {
        'success': True,
        'message': message
    }

    if data is not None:
        response['data'] = data

    return jsonify(response), status_code


def error_response(message: str, status_code: int = 400, errors: Optional[Dict] = None):
    """
    Create a standardized error response.

    Args:
        message: Error message
        status_code: HTTP status code
        errors: Optional dictionary of field-specific errors

    Returns:
        Flask JSON response
    """
    response = {
        'success': False,
        'message': message
    }

    if errors:
        response['errors'] = errors

    return jsonify(response), status_code


def validation_error_response(errors: Dict[str, str], status_code: int = 400):
    """
    Create a validation error response.

    Args:
        errors: Dictionary of field names to error messages
        status_code: HTTP status code

    Returns:
        Flask JSON response
    """
    return error_response("Validation failed", status_code, errors)


def not_found_response(resource: str = "Resource"):
    """
    Create a not found error response.

    Args:
        resource: Name of the resource that wasn't found

    Returns:
        Flask JSON response with 404 status
    """
    return error_response(f"{resource} not found", 404)


def unauthorized_response(message: str = "Unauthorized"):
    """
    Create an unauthorized error response.

    Args:
        message: Error message

    Returns:
        Flask JSON response with 401 status
    """
    return error_response(message, 401)


def forbidden_response(message: str = "Insufficient permissions"):
    """
    Create a forbidden error response.

    Args:
        message: Error message

    Returns:
        Flask JSON response with 403 status
    """
    return error_response(message, 403)
