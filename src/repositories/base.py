"""Base repository with common CRUD operations."""
from typing import Optional, Dict, List, Any
from src.database.connection import get_db_cursor


class BaseRepository:
    """Base repository class with common database operations."""

    def __init__(self, table_name: str, id_column: str):
        """
        Initialize base repository.

        Args:
            table_name: Name of the database table
            id_column: Name of the primary key column
        """
        self.table_name = table_name
        self.id_column = id_column

    def _row_to_dict(self, cursor, row) -> Optional[Dict]:
        """
        Convert database row to dictionary.

        Args:
            cursor: Database cursor with description
            row: Database row tuple

        Returns:
            Dictionary with column names as keys, or None if row is None
        """
        if row is None:
            return None

        return {desc[0]: value for desc, value in zip(cursor.description, row)}

    def _rows_to_dicts(self, cursor, rows) -> List[Dict]:
        """
        Convert multiple database rows to list of dictionaries.

        Args:
            cursor: Database cursor with description
            rows: List of database row tuples

        Returns:
            List of dictionaries
        """
        return [self._row_to_dict(cursor, row) for row in rows]

    def find_by_id(self, id_value: Any) -> Optional[Dict]:
        """
        Find a record by its primary key.

        Args:
            id_value: Value of the primary key

        Returns:
            Dictionary representing the record, or None if not found
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE {self.id_column} = %s",
                (id_value,)
            )
            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)

    def find_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Find all records with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of dictionaries representing records
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {self.table_name} ORDER BY {self.id_column} LIMIT %s OFFSET %s",
                (limit, offset)
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)

    def find_by_field(self, field: str, value: Any) -> Optional[Dict]:
        """
        Find a single record by a specific field.

        Args:
            field: Field name
            value: Field value

        Returns:
            Dictionary representing the record, or None if not found
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE {field} = %s LIMIT 1",
                (value,)
            )
            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)

    def find_all_by_field(self, field: str, value: Any) -> List[Dict]:
        """
        Find all records matching a specific field value.

        Args:
            field: Field name
            value: Field value

        Returns:
            List of dictionaries representing matching records
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE {field} = %s",
                (value,)
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)

    def insert(self, data: Dict) -> Optional[int]:
        """
        Insert a new record.

        Args:
            data: Dictionary of field names to values

        Returns:
            ID of the inserted record, or None if insert failed
        """
        if not data:
            return None

        fields = list(data.keys())
        placeholders = ', '.join(['%s'] * len(fields))
        fields_str = ', '.join(fields)

        with get_db_cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {self.table_name} ({fields_str})
                VALUES ({placeholders})
                RETURNING {self.id_column}
                """,
                list(data.values())
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def update(self, id_value: Any, data: Dict) -> bool:
        """
        Update a record by its primary key.

        Args:
            id_value: Value of the primary key
            data: Dictionary of field names to new values

        Returns:
            True if update was successful, False otherwise
        """
        if not data:
            return False

        set_clause = ', '.join([f"{field} = %s" for field in data.keys()])
        values = list(data.values()) + [id_value]

        with get_db_cursor() as cursor:
            cursor.execute(
                f"UPDATE {self.table_name} SET {set_clause} WHERE {self.id_column} = %s",
                values
            )
            return cursor.rowcount > 0

    def delete(self, id_value: Any) -> bool:
        """
        Delete a record by its primary key.

        Args:
            id_value: Value of the primary key

        Returns:
            True if deletion was successful, False otherwise
        """
        with get_db_cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE {self.id_column} = %s",
                (id_value,)
            )
            return cursor.rowcount > 0

    def count(self) -> int:
        """
        Count total number of records.

        Returns:
            Total count of records
        """
        with get_db_cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            result = cursor.fetchone()
            return result[0] if result else 0
