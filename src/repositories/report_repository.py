"""Report repository for sales and analytics."""
from typing import List, Dict
from datetime import datetime
from src.database.connection import get_db_cursor


class ReportRepository:
    """Repository for reporting and analytics."""

    def get_sales_by_period(self, start_date: datetime, end_date: datetime,
                           group_by: str = 'day') -> List[Dict]:
        """
        Get sales aggregated by time period (SPEC.md lines 180-188).

        Args:
            start_date: Start date
            end_date: End date
            group_by: Grouping ('day', 'week', 'month')

        Returns:
            List of sales data by period
        """
        date_trunc_map = {
            'day': 'day',
            'week': 'week',
            'month': 'month'
        }

        trunc = date_trunc_map.get(group_by, 'day')

        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                f"""
                SELECT
                    DATE_TRUNC(%s, order_date) as period,
                    SUM(total_amount) as total_sales,
                    COUNT(*) as orders_count,
                    AVG(total_amount) as avg_order_value
                FROM kitch_order
                WHERE order_date BETWEEN %s AND %s
                    AND payment_status != 'cancelled'
                GROUP BY DATE_TRUNC(%s, order_date)
                ORDER BY period
                """,
                (trunc, start_date, end_date, trunc)
            )
            rows = cursor.fetchall()
            return [
                {
                    'period': row[0].isoformat() if row[0] else None,
                    'total_sales': float(row[1]) if row[1] else 0,
                    'orders_count': row[2] if row[2] else 0,
                    'avg_order_value': float(row[3]) if row[3] else 0
                }
                for row in rows
            ]

    def get_top_selling_items(self, start_date: datetime = None,
                             end_date: datetime = None, limit: int = 5) -> List[Dict]:
        """
        Get top selling items (SPEC.md lines 191-201).

        Args:
            start_date: Optional start date
            end_date: Optional end date
            limit: Number of items to return

        Returns:
            List of top items with sales data
        """
        query = """
            SELECT
                oi.kic_id,
                oi.name,
                SUM(oi.line_total) as total_sales,
                SUM(oi.quantity) as quantity_sold,
                COUNT(DISTINCT oi.order_id) as orders_count
            FROM kitch_order_item oi
            JOIN kitch_order o ON oi.order_id = o.order_id
            WHERE o.payment_status != 'cancelled'
        """
        params = []

        if start_date:
            query += " AND o.order_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND o.order_date <= %s"
            params.append(end_date)

        query += """
            GROUP BY oi.kic_id, oi.name
            ORDER BY total_sales DESC
            LIMIT %s
        """
        params.append(limit)

        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                {
                    'kic_id': row[0],
                    'name': row[1],
                    'total_sales': float(row[2]) if row[2] else 0,
                    'quantity_sold': row[3] if row[3] else 0,
                    'orders_count': row[4] if row[4] else 0
                }
                for row in rows
            ]

    def get_top_customers(self, start_date: datetime = None,
                         end_date: datetime = None, limit: int = 5) -> List[Dict]:
        """
        Get top customers by spending (SPEC.md lines 203-209).

        Args:
            start_date: Optional start date
            end_date: Optional end date
            limit: Number of customers to return

        Returns:
            List of top customers with spending data
        """
        query = """
            SELECT
                c.cust_id,
                c.cust_name,
                c.cust_phone_number,
                SUM(o.total_amount) as total_spent,
                COUNT(o.order_id) as order_count,
                AVG(o.total_amount) as avg_order_value
            FROM kitch_order o
            JOIN kitch_customer c ON o.cust_id = c.cust_id
            WHERE o.payment_status != 'cancelled'
        """
        params = []

        if start_date:
            query += " AND o.order_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND o.order_date <= %s"
            params.append(end_date)

        query += """
            GROUP BY c.cust_id, c.cust_name, c.cust_phone_number
            ORDER BY total_spent DESC
            LIMIT %s
        """
        params.append(limit)

        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                {
                    'cust_id': row[0],
                    'cust_name': row[1],
                    'cust_phone_number': row[2],
                    'total_spent': float(row[3]) if row[3] else 0,
                    'order_count': row[4] if row[4] else 0,
                    'avg_order_value': float(row[5]) if row[5] else 0
                }
                for row in rows
            ]

    def get_sales_summary(self, start_date: datetime = None,
                         end_date: datetime = None) -> Dict:
        """
        Get overall sales summary.

        Args:
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Dictionary with summary statistics
        """
        query = """
            SELECT
                COUNT(*) as total_orders,
                SUM(total_amount) as total_sales,
                AVG(total_amount) as avg_order_value,
                SUM(tip_amount) as total_tips,
                SUM(discount_amount) as total_discounts
            FROM kitch_order
            WHERE payment_status != 'cancelled'
        """
        params = []

        if start_date:
            query += " AND order_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND order_date <= %s"
            params.append(end_date)

        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()

            if row:
                return {
                    'total_orders': row[0] if row[0] else 0,
                    'total_sales': float(row[1]) if row[1] else 0,
                    'avg_order_value': float(row[2]) if row[2] else 0,
                    'total_tips': float(row[3]) if row[3] else 0,
                    'total_discounts': float(row[4]) if row[4] else 0
                }

            return {
                'total_orders': 0,
                'total_sales': 0,
                'avg_order_value': 0,
                'total_tips': 0,
                'total_discounts': 0
            }
