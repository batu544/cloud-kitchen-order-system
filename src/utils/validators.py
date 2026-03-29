"""Input validation utilities."""
import re
from typing import Tuple, List, Dict, Any


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Validate and normalize phone number to exactly 10 digits (SPEC.md line 117).

    Args:
        phone: Phone number string

    Returns:
        Tuple of (is_valid, normalized_phone_or_error_message)
    """
    if not phone:
        return False, "Phone number is required"

    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)

    if len(digits) != 10:
        return False, "Phone number must be exactly 10 digits"

    return True, digits


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.

    Args:
        email: Email address string

    Returns:
        Tuple of (is_valid, error_message_or_empty)
    """
    if not email:
        return False, "Email is required"

    # Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"

    return True, ""


def validate_order_items(items: List[Dict[str, Any]]) -> List[str]:
    """
    Validate order items structure.

    Args:
        items: List of order item dictionaries

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    if not items or len(items) == 0:
        errors.append("At least one item is required")
        return errors

    for idx, item in enumerate(items):
        item_num = idx + 1

        # Check required fields
        if 'kic_id' not in item:
            errors.append(f"Item {item_num}: kic_id is required")

        if 'quantity' in item:
            try:
                qty = int(item['quantity'])
                if qty <= 0:
                    errors.append(f"Item {item_num}: quantity must be greater than 0")
            except (ValueError, TypeError):
                errors.append(f"Item {item_num}: quantity must be a number")

        # Validate catering fields
        if item.get('is_catering'):
            if 'catering_size' not in item:
                errors.append(f"Item {item_num}: catering_size required for catering items")
            elif item['catering_size'] not in ['small', 'medium', 'large']:
                errors.append(f"Item {item_num}: catering_size must be 'small', 'medium', or 'large'")

    return errors


def validate_discount(discount_type: str, discount_value: float) -> List[str]:
    """
    Validate discount parameters.

    Args:
        discount_type: 'percent' or 'fixed'
        discount_value: Discount amount

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    if discount_type not in ['percent', 'fixed']:
        errors.append("Discount type must be 'percent' or 'fixed'")

    if discount_value < 0:
        errors.append("Discount value cannot be negative")

    if discount_type == 'percent' and discount_value > 100:
        errors.append("Percent discount cannot exceed 100%")

    return errors


def validate_payment_method(method: str) -> Tuple[bool, str]:
    """
    Validate payment method.

    Args:
        method: Payment method string

    Returns:
        Tuple of (is_valid, error_message_or_empty)
    """
    valid_methods = ['cash', 'card', 'other']
    if method not in valid_methods:
        return False, f"Payment method must be one of: {', '.join(valid_methods)}"
    return True, ""


def validate_payment_status(status: str) -> Tuple[bool, str]:
    """
    Validate payment status.

    Args:
        status: Payment status string

    Returns:
        Tuple of (is_valid, error_message_or_empty)
    """
    valid_statuses = ['pending', 'paid', 'partially_paid', 'refunded', 'cancelled']
    if status not in valid_statuses:
        return False, f"Payment status must be one of: {', '.join(valid_statuses)}"
    return True, ""
