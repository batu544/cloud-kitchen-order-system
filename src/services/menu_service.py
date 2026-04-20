"""Menu service for menu and category management."""
from typing import Dict, Optional, Tuple
from src.repositories.menu_repository import MenuRepository


class MenuService:
    """Service for menu operations."""

    def __init__(self):
        self.menu_repo = MenuRepository()

    def get_full_menu(self, category_id: int = None, is_catering: bool = None) -> Dict:
        """
        Get full menu with categories and items.

        Args:
            category_id: Optional category filter
            is_catering: Optional catering items filter

        Returns:
            Dictionary with categories and items
        """
        categories = self.menu_repo.get_all_categories()
        items = self.menu_repo.get_all_items(
            category_id=category_id,
            is_catering=is_catering,
            is_active=True
        )

        # Group items by category
        items_by_category = {}
        for item in items:
            cat_id = item['category_id']
            if cat_id not in items_by_category:
                items_by_category[cat_id] = []
            items_by_category[cat_id].append(item)

        return {
            'categories': categories,
            'items': items,
            'items_by_category': items_by_category
        }

    def get_item(self, kic_id: int) -> Optional[Dict]:
        """
        Get menu item by ID.

        Args:
            kic_id: Item ID

        Returns:
            Item dictionary or None
        """
        return self.menu_repo.get_item_by_id(kic_id)

    def create_item(self, name: str, price: float, category_id: int,
                   description: str = None, is_catering: bool = False,
                   image_url: str = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create new menu item (admin only).

        Args:
            name: Item name
            price: Item price
            category_id: Category ID
            description: Optional description
            is_catering: Whether item is catering
            image_url: Optional image URL

        Returns:
            Tuple of (success, message, item_id)
        """
        if price < 0:
            return False, "Price cannot be negative", None

        try:
            item_id = self.menu_repo.create_item(
                name=name,
                price=price,
                category_id=category_id,
                description=description,
                is_catering=is_catering,
                image_url=image_url
            )

            if item_id:
                return True, "Menu item created", item_id
            else:
                return False, "Failed to create menu item", None

        except Exception as e:
            return False, f"Error creating menu item: {str(e)}", None

    def update_item(self, kic_id: int, **kwargs) -> Tuple[bool, str]:
        """
        Update menu item (admin only).

        Args:
            kic_id: Item ID
            **kwargs: Fields to update

        Returns:
            Tuple of (success, message)
        """
        success = self.menu_repo.update_item(kic_id, **kwargs)

        if success:
            return True, "Menu item updated"
        else:
            return False, "Failed to update menu item"
