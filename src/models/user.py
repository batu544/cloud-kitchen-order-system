"""User and authentication data models."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User model for authentication and authorization."""
    user_id: int
    username: str
    role: str  # 'customer', 'staff', 'admin'
    cust_id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for API responses."""
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'cust_id': self.cust_id,
            'is_active': self.is_active,
        }

        if include_sensitive:
            data['created_at'] = self.created_at.isoformat() if self.created_at else None
            data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None

        return data

    def is_customer(self) -> bool:
        """Check if user is a customer."""
        return self.role == 'customer'

    def is_staff(self) -> bool:
        """Check if user is staff."""
        return self.role == 'staff'

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == 'admin'

    def has_permission(self, required_role: str) -> bool:
        """
        Check if user has required permission level.

        Permission hierarchy: admin > staff > customer
        """
        role_hierarchy = {'customer': 0, 'staff': 1, 'admin': 2}
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        return user_level >= required_level
