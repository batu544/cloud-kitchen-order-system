"""Unit tests for report_service.py with mocked repositories."""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


class TestReportService(unittest.TestCase):

    def setUp(self):
        self.report_repo_patcher = patch('src.services.report_service.ReportRepository')
        self.MockReportRepo = self.report_repo_patcher.start()
        
        self.mock_report_repo = MagicMock()
        self.MockReportRepo.return_value = self.mock_report_repo

        from src.services.report_service import ReportService
        self.service = ReportService()

    def tearDown(self):
        self.report_repo_patcher.stop()

    def test_get_sales_report_defaults(self):
        # Mock repo responses
        self.mock_report_repo.get_sales_by_period.return_value = [{'date': '2023-01-01', 'sales': 100}]
        self.mock_report_repo.get_sales_summary.return_value = {'total_sales': 100}

        report = self.service.get_sales_report()

        self.assertIn('period', report)
        self.assertIn('summary', report)
        self.assertIn('data', report)
        self.assertEqual(report['summary']['total_sales'], 100)
        self.mock_report_repo.get_sales_by_period.assert_called_once()
        self.mock_report_repo.get_sales_summary.assert_called_once()

    def test_get_sales_report_with_dates(self):
        start_date = "2023-01-01"
        end_date = "2023-01-31"
        self.mock_report_repo.get_sales_by_period.return_value = []
        self.mock_report_repo.get_sales_summary.return_value = {}

        report = self.service.get_sales_report(start_date=start_date, end_date=end_date)

        self.assertEqual(report['period']['start'], datetime.fromisoformat(start_date).isoformat())
        self.assertEqual(report['period']['end'], datetime.fromisoformat(end_date).isoformat())

    def test_get_top_items_report(self):
        self.mock_report_repo.get_top_selling_items.return_value = [{'item': 'Pizza', 'count': 10}]
        
        report = self.service.get_top_items_report(limit=3)

        self.assertEqual(len(report['items']), 1)
        self.assertEqual(report['limit'], 3)
        self.mock_report_repo.get_top_selling_items.assert_called_once()

    def test_get_top_customers_report(self):
        self.mock_report_repo.get_top_customers.return_value = [{'customer': 'Alice', 'total': 500}]
        
        report = self.service.get_top_customers_report(limit=10)

        self.assertEqual(len(report['customers']), 1)
        self.assertEqual(report['limit'], 10)
        self.mock_report_repo.get_top_customers.assert_called_once()

    def test_get_orders_report(self):
        self.mock_report_repo.get_orders_report.return_value = [{'order_id': 1}]
        
        report = self.service.get_orders_report()

        self.assertIn('orders', report)
        self.assertEqual(len(report['orders']), 1)
        self.mock_report_repo.get_orders_report.assert_called_once()

    def test_get_pending_payments_report(self):
        self.mock_report_repo.get_pending_payments.return_value = [{'order_id': 2}]
        
        report = self.service.get_pending_payments_report()

        self.assertIn('orders', report)
        self.assertEqual(len(report['orders']), 1)
        self.mock_report_repo.get_pending_payments.assert_called_once()


if __name__ == '__main__':
    unittest.main()
