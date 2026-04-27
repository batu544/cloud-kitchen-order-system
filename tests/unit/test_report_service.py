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

        # Start date should be 2023-01-01T00:00:00
        self.assertTrue(report['period']['start'].startswith("2023-01-01T00:00:00"))
        # End date should be 2023-01-31T23:59:59.999999
        self.assertTrue(report['period']['end'].startswith("2023-01-31T23:59:59.999999"))

    def test_parse_date_logic(self):
        # Start date (no is_end)
        dt = self.service._parse_date("2023-01-01")
        self.assertEqual(dt.hour, 0)
        
        # End date (is_end=True, no time in string)
        dt = self.service._parse_date("2023-01-01", is_end=True)
        self.assertEqual(dt.hour, 23)
        self.assertEqual(dt.minute, 59)
        self.assertEqual(dt.microsecond, 999999)
        
        # End date with time already provided (should NOT override)
        # Note: len("2023-01-01T12:00:00") > 10
        dt = self.service._parse_date("2023-01-01T12:00:00", is_end=True)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 0)

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
