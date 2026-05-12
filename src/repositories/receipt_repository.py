"""Receipt repository for managing operating expense receipts."""
from typing import List, Dict, Optional
from datetime import datetime
from src.database.connection import get_db_cursor
from src.repositories.base import BaseRepository


class ReceiptRepository(BaseRepository):
    """Repository for managing kitch_receipt and kitch_receipt_item tables."""

    def __init__(self):
        super().__init__('kitch_receipt', 'receipt_id')

    def create_receipt_with_items(self, receipt_data: Dict, items: List[Dict]) -> Optional[int]:
        """
        Create a receipt and all its line items in a single transaction.

        Args:
            receipt_data: Metadata for the receipt
            items: List of line items

        Returns:
            ID of the created receipt
        """
        with get_db_cursor(commit=True) as cursor:
            # 1. Insert receipt metadata
            fields = list(receipt_data.keys())
            placeholders = ', '.join(['%s'] * len(fields))
            fields_str = ', '.join(fields)
            
            cursor.execute(
                f"""
                INSERT INTO kitch_receipt ({fields_str})
                VALUES ({placeholders})
                RETURNING receipt_id
                """,
                list(receipt_data.values())
            )
            receipt_id = cursor.fetchone()[0]

            # 2. Insert line items
            if items:
                for item in items:
                    item['receipt_id'] = receipt_id
                    item_fields = list(item.keys())
                    item_placeholders = ', '.join(['%s'] * len(item_fields))
                    item_fields_str = ', '.join(item_fields)
                    
                    cursor.execute(
                        f"""
                        INSERT INTO kitch_receipt_item ({item_fields_str})
                        VALUES ({item_placeholders})
                        """,
                        list(item.values())
                    )
            
            return receipt_id

    def get_receipt_with_items(self, receipt_id: int) -> Optional[Dict]:
        """Get receipt metadata and all its items."""
        receipt = self.find_by_id(receipt_id)
        if not receipt:
            return None

        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM kitch_receipt_item WHERE receipt_id = %s",
                (receipt_id,)
            )
            rows = cursor.fetchall()
            receipt['items'] = self._rows_to_dicts(cursor, rows)
            
        return receipt

    def get_monthly_expenditure(self, year: int, month: int) -> List[Dict]:
        """Get total expenditure grouped by receipt for a specific month."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT 
                    receipt_id, shop_name, receipt_date, total_amount, image_path
                FROM kitch_receipt
                WHERE EXTRACT(YEAR FROM receipt_date) = %s 
                  AND EXTRACT(MONTH FROM receipt_date) = %s
                ORDER BY receipt_date DESC
                """,
                (year, month)
            )
            rows = cursor.fetchall()
            return self._rows_to_dicts(cursor, rows)

    def get_expenditure_summary(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get total expenditure summary for a date range."""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_receipts,
                    COALESCE(SUM(total_amount), 0) as total_spent,
                    COALESCE(AVG(total_amount), 0) as avg_receipt_value
                FROM kitch_receipt
                WHERE receipt_date BETWEEN %s AND %s
                """,
                (start_date, end_date)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'total_receipts': row[0],
                    'total_spent': float(row[1]),
                    'avg_receipt_value': float(row[2])
                }
            return {'total_receipts': 0, 'total_spent': 0, 'avg_receipt_value': 0}
