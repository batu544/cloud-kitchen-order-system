"""Payment data model."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Payment:
    """Payment model."""
    payment_id: Optional[int]
    order_id: int
    amount: Decimal
    payment_method: str  # 'cash', 'card', 'other'
    payment_status: str  # 'pending', 'paid', 'partially_paid', 'refunded'
    payment_date: Optional[datetime] = None
    tip_amount: Decimal = Decimal('0')
    payment_notes: Optional[str] = None
    recorded_by_user_id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'payment_id': self.payment_id,
            'order_id': self.order_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'tip_amount': float(self.tip_amount),
            'payment_notes': self.payment_notes,
            'recorded_by_user_id': self.recorded_by_user_id,
        }
