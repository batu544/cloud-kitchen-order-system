"""Menu repository for categories and items."""
from typing import Optional, Dict, List
from src.repositories.base import BaseRepository
from src.database.connection import get_db_cursor


class MenuRepository(BaseRepository):
    """Repository for menu operations."""

    def __init__(self):
        super().__init__('kitch_item_catalg', 'kic_id')

    def get_all_categories(self) -> List[Dict]:
        """
        Get all menu categories.

        Returns:
            List of category dictionaries
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM kitch_category ORDER BY category_name"
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)

    def get_category_by_id(self, category_id: int) -> Optional[Dict]:
        """
        Get category by ID.

        Args:
            category_id: Category ID

        Returns:
            Category dictionary or None
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM kitch_category WHERE category_id = %s",
                (category_id,)
            )
            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)

    def get_all_items(self, category_id: int = None, is_catering: bool = None,
                      is_active: bool = True) -> List[Dict]:
        """
        Get menu items with optional filters.

        Args:
            category_id: Optional category filter
            is_catering: Optional catering items filter
            is_active: Filter by active status (default True)

        Returns:
            List of menu item dictionaries with category names
        """
        query = """
            SELECT i.*, c.category_name
            FROM kitch_item_catalg i
            LEFT JOIN kitch_category c ON i.category_id = c.category_id
            WHERE 1=1
        """
        params = []

        if is_active is not None:
            query += " AND i.is_active = %s"
            params.append(is_active)

        if category_id is not None:
            query += " AND i.category_id = %s"
            params.append(category_id)

        if is_catering is not None:
            query += " AND i.is_catering = %s"
            params.append(is_catering)

        query += " ORDER BY c.category_name, i.kic_name"

        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)

    def get_item_by_id(self, kic_id: int) -> Optional[Dict]:
        """
        Get menu item by ID with category name.

        Args:
            kic_id: Item ID

        Returns:
            Item dictionary with category name or None
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT i.*, c.category_name
                FROM kitch_item_catalg i
                LEFT JOIN kitch_category c ON i.category_id = c.category_id
                WHERE i.kic_id = %s
                """,
                (kic_id,)
            )
            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)

    def create_item(self, name: str, price: float, category_id: int,
                   description: str = None, is_catering: bool = False,
                   image_url: str = None) -> Optional[int]:
        """
        Create a new menu item.

        Args:
            name: Item name
            price: Item price
            category_id: Category ID
            description: Optional description
            is_catering: Whether item is catering
            image_url: Optional image URL

        Returns:
            New item ID or None
        """
        data = {
            'kic_name': name,
            'kic_price': price,
            'category_id': category_id,
            'description': description,
            'is_catering': is_catering,
            'is_active': True,
            'image_url': image_url
        }
        return self.insert(data)

    def update_item(self, kic_id: int, name: str = None, price: float = None,
                   category_id: int = None, description: str = None,
                   is_catering: bool = None, is_active: bool = None,
                   image_url: str = None) -> bool:
        """
        Update menu item.

        Args:
            kic_id: Item ID
            name: Optional new name
            price: Optional new price
            category_id: Optional new category
            description: Optional new description
            is_catering: Optional catering flag
            is_active: Optional active flag
            image_url: Optional new image URL

        Returns:
            True if successful
        """
        data = {'updated_at': 'CURRENT_TIMESTAMP'}

        if name is not None:
            data['kic_name'] = name
        if price is not None:
            data['kic_price'] = price
        if category_id is not None:
            data['category_id'] = category_id
        if description is not None:
            data['description'] = description
        if is_catering is not None:
            data['is_catering'] = is_catering
        if is_active is not None:
            data['is_active'] = is_active
        if image_url is not None:
            data['image_url'] = image_url

        return self.update(kic_id, data)

    def get_items_by_ids(self, kic_ids: List[int]) -> List[Dict]:
        """
        Get multiple items by their IDs.

        Args:
            kic_ids: List of item IDs

        Returns:
            List of item dictionaries
        """
        if not kic_ids:
            return []

        with get_db_cursor() as cursor:
            placeholders = ','.join(['%s'] * len(kic_ids))
            cursor.execute(
                f"""
                SELECT i.*, c.category_name
                FROM kitch_item_catalg i
                LEFT JOIN kitch_category c ON i.category_id = c.category_id
                WHERE i.kic_id IN ({placeholders})
                """,
                kic_ids
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)
