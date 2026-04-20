"""Pricing service for catering calculations and discounts (SPEC.md lines 119-147)."""
from decimal import Decimal
from typing import Tuple


def calculate_catering_price(base_price: Decimal, size: str) -> Decimal:
    """
    Calculate catering tray price based on size (SPEC.md lines 130-147).

    Formulas:
    - small: base_price * 4 * 0.9
    - medium: base_price * 6 * 0.9
    - large: base_price * 12 * 0.9

    Args:
        base_price: Base plate price from menu
        size: Catering size ('small', 'medium', 'large')

    Returns:
        Calculated catering price

    Raises:
        ValueError: If size is invalid
    """
    multipliers = {
        'small': 4,
        'medium': 6,
        'large': 12
    }

    if size not in multipliers:
        raise ValueError(f"Invalid catering size: {size}. Must be 'small', 'medium', or 'large'")

    multiplier = multipliers[size]
    catering_price = base_price * multiplier * Decimal('0.9')

    return catering_price.quantize(Decimal('0.01'))


def apply_discount(subtotal: Decimal, discount_type: str, discount_value: Decimal) -> Decimal:
    """
    Apply discount to subtotal (SPEC.md lines 119-123).

    Discount types:
    - percent: discount_value is percentage (0-100)
    - fixed: discount_value is currency amount

    Args:
        subtotal: Order subtotal before discount
        discount_type: 'percent' or 'fixed'
        discount_value: Discount amount or percentage

    Returns:
        Discount amount to subtract from subtotal

    Raises:
        ValueError: If discount_type is invalid
    """
    if discount_type not in ['percent', 'fixed']:
        raise ValueError(f"Invalid discount type: {discount_type}. Must be 'percent' or 'fixed'")

    if discount_type == 'percent':
        if discount_value < 0 or discount_value > 100:
            raise ValueError(f"Percent discount must be between 0 and 100, got {discount_value}")
        discount_amount = subtotal * (discount_value / 100)
    elif discount_type == 'fixed':
        if discount_value < 0:
            raise ValueError(f"Fixed discount cannot be negative, got {discount_value}")
        # Don't let discount exceed subtotal
        discount_amount = min(discount_value, subtotal)
    else:
        discount_amount = Decimal('0')

    return discount_amount.quantize(Decimal('0.01'))


def calculate_order_total(
    subtotal: Decimal,
    discount_amount: Decimal,
    tip_amount: Decimal
) -> Tuple[Decimal, Decimal]:
    """
    Calculate final order total (SPEC.md line 123).

    Order of calculation: subtotal → discount → tip → total_amount
    (No tax per user requirement)

    Args:
        subtotal: Sum of all line item totals
        discount_amount: Discount to apply
        tip_amount: Tip amount to add

    Returns:
        Tuple of (tax_amount, total_amount)
    """
    # Ensure all values are non-negative
    subtotal = max(subtotal, Decimal('0'))
    discount_amount = max(discount_amount, Decimal('0'))
    tip_amount = max(tip_amount, Decimal('0'))

    # Calculate after discount
    after_discount = max(subtotal - discount_amount, Decimal('0'))

    # No tax per user requirement
    tax_amount = Decimal('0')

    # Final total
    total_amount = after_discount + tax_amount + tip_amount

    return (
        tax_amount.quantize(Decimal('0.01')),
        total_amount.quantize(Decimal('0.01'))
    )


def calculate_line_total(unit_price: Decimal, quantity: int, is_catering: bool = False,
                         catering_size: str = None) -> Decimal:
    """
    Calculate line item total.

    Args:
        unit_price: Base unit price
        quantity: Number of items
        is_catering: Whether this is a catering item
        catering_size: Size if catering ('small', 'medium', 'large')

    Returns:
        Line item total
    """
    if is_catering and catering_size:
        # Calculate catering price (which already includes quantity logic)
        item_price = calculate_catering_price(unit_price, catering_size)
        line_total = item_price * quantity
    else:
        # Regular item
        line_total = unit_price * quantity

    return line_total.quantize(Decimal('0.01'))
