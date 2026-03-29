"""Order data models."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List


@dataclass
class OrderItem:
    """Order item model."""
    order_item_id: Optional[int]
    order_id: Optional[int]
    kic_id: int
    name: str
    unit_price: Decimal
    quantity: int = 1
    special_instructions: Optional[str] = None
    is_catering: bool = False
    catering_size: Optional[str] = None  # 'small', 'medium', 'large'
    line_total: Decimal = Decimal('0')
    created_at: Optional[datetime] = None

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'order_item_id': self.order_item_id,
            'order_id': self.order_id,
            'kic_id': self.kic_id,
            'name': self.name,
            'unit_price': float(self.unit_price),
            'quantity': self.quantity,
            'special_instructions': self.special_instructions,
            'is_catering': self.is_catering,
            'catering_size': self.catering_size,
            'line_total': float(self.line_total),
        }


@dataclass
class OrderStatusHistory:
    """Order status history model."""
    id: Optional[int]
    order_id: int
    status_id: int
    changed_by_user_id: Optional[int]
    changed_at: datetime
    note: Optional[str] = None
    status_name: Optional[str] = None  # Joined from status table

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'status_id': self.status_id,
            'status_name': self.status_name,
            'changed_by_user_id': self.changed_by_user_id,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'note': self.note,
        }


@dataclass
class Order:
    """Order model."""
    order_id: Optional[int]
    order_ref: str
    order_phone: str
    subtotal: Decimal
    total_amount: Decimal
    cust_id: Optional[int] = None
    placed_by_user_id: Optional[int] = None
    order_date: Optional[datetime] = None
    discount_amount: Decimal = Decimal('0')
    discount_type: Optional[str] = None  # 'percent' or 'fixed'
    tip_amount: Decimal = Decimal('0')
    tax_amount: Decimal = Decimal('0')
    payment_status: str = 'pending'
    current_status_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Related data (not in DB)
    items: List[OrderItem] = field(default_factory=list)
    status_history: List[OrderStatusHistory] = field(default_factory=list)
    cust_name: Optional[str] = None  # Joined from customer table
    current_status_name: Optional[str] = None  # Joined from status table

    def to_dict(self, include_items=True, include_history=False):
        """Convert to dictionary for API responses."""
        data = {
            'order_id': self.order_id,
            'order_ref': self.order_ref,
            'cust_id': self.cust_id,
            'cust_name': self.cust_name,
            'order_phone': self.order_phone,
            'placed_by_user_id': self.placed_by_user_id,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'subtotal': float(self.subtotal),
            'discount_amount': float(self.discount_amount),
            'discount_type': self.discount_type,
            'tip_amount': float(self.tip_amount),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'payment_status': self.payment_status,
            'current_status_id': self.current_status_id,
            'current_status_name': self.current_status_name,
            'notes': self.notes,
        }

        if include_items:
            data['items'] = [item.to_dict() for item in self.items]

        if include_history:
            data['status_history'] = [status.to_dict() for status in self.status_history]

        return data
