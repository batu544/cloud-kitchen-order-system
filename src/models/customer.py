"""Customer data model."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Customer:
    """Customer model."""
    cust_id: int
    cust_name: str
    cust_phone_number: str
    cust_email: Optional[str] = None
    cust_address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'cust_id': self.cust_id,
            'cust_name': self.cust_name,
            'cust_phone_number': self.cust_phone_number,
            'cust_email': self.cust_email,
            'cust_address': self.cust_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
