"""Report service for analytics and reporting."""
from datetime import datetime, timedelta
from typing import Dict, Optional
from src.repositories.report_repository import ReportRepository


class ReportService:
    """Service for reporting operations."""

    def __init__(self):
        self.report_repo = ReportRepository()

    def get_sales_report(self, start_date: str = None, end_date: str = None,
                        group_by: str = 'day') -> Dict:
        """
        Get sales report by period.

        Args:
            start_date: Start date (ISO format or None for last 30 days)
            end_date: End date (ISO format or None for today)
            group_by: Grouping ('day', 'week', 'month')

        Returns:
            Sales report dictionary
        """
        # Default to last 30 days if not specified
        if not end_date:
            end_datetime = datetime.now()
        else:
            end_datetime = datetime.fromisoformat(end_date)

        if not start_date:
            start_datetime = end_datetime - timedelta(days=30)
        else:
            start_datetime = datetime.fromisoformat(start_date)

        sales_data = self.report_repo.get_sales_by_period(
            start_datetime, end_datetime, group_by
        )

        summary = self.report_repo.get_sales_summary(start_datetime, end_datetime)

        return {
            'period': {
                'start': start_datetime.isoformat(),
                'end': end_datetime.isoformat(),
                'group_by': group_by
            },
            'summary': summary,
            'data': sales_data
        }

    def get_top_items_report(self, start_date: str = None, end_date: str = None,
                            limit: int = 5) -> Dict:
        """
        Get top selling items report.

        Args:
            start_date: Optional start date
            end_date: Optional end date
            limit: Number of items to return

        Returns:
            Top items report
        """
        start_datetime = datetime.fromisoformat(start_date) if start_date else None
        end_datetime = datetime.fromisoformat(end_date) if end_date else None

        top_items = self.report_repo.get_top_selling_items(
            start_datetime, end_datetime, limit
        )

        return {
            'period': {
                'start': start_date,
                'end': end_date
            },
            'limit': limit,
            'items': top_items
        }

    def get_top_customers_report(self, start_date: str = None, end_date: str = None,
                                limit: int = 5) -> Dict:
        """
        Get top customers report.

        Args:
            start_date: Optional start date
            end_date: Optional end date
            limit: Number of customers to return

        Returns:
            Top customers report
        """
        start_datetime = datetime.fromisoformat(start_date) if start_date else None
        end_datetime = datetime.fromisoformat(end_date) if end_date else None

        top_customers = self.report_repo.get_top_customers(
            start_datetime, end_datetime, limit
        )

        return {
            'period': {
                'start': start_date,
                'end': end_date
            },
            'limit': limit,
            'customers': top_customers
        }
