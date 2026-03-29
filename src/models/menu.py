"""Menu and category data models."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Category:
    """Menu category model."""
    category_id: int
    category_name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'category_id': self.category_id,
            'category_name': self.category_name,
            'description': self.description,
        }


@dataclass
class MenuItem:
    """Menu item model."""
    kic_id: int
    kic_name: str
    kic_price: Decimal
    category_id: int
    description: Optional[str] = None
    is_catering: bool = False
    is_active: bool = True
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    category_name: Optional[str] = None  # Joined from category table

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'kic_id': self.kic_id,
            'kic_name': self.kic_name,
            'kic_price': float(self.kic_price),
            'category_id': self.category_id,
            'category_name': self.category_name,
            'description': self.description,
            'is_catering': self.is_catering,
            'is_active': self.is_active,
            'image_url': self.image_url,
        }
