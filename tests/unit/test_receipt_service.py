"""Unit tests for receipt_service.py with mocked repositories and AI."""
import unittest
from unittest.mock import MagicMock, patch, mock_open
import json
from datetime import datetime


class TestReceiptService(unittest.TestCase):

    def setUp(self):
        # Patch dependencies
        self.repo_patcher = patch('src.services.receipt_service.ReceiptRepository')
        self.MockRepo = self.repo_patcher.start()
        self.mock_repo = MagicMock()
        self.MockRepo.return_value = self.mock_repo

        self.ai_patcher = patch('src.services.receipt_service.genai')
        self.mock_ai = self.ai_patcher.start()

        # Import service after patching
        from src.services.receipt_service import ReceiptService
        with patch('src.services.receipt_service.Config') as mock_config:
            mock_config.GOOGLE_API_KEY = "fake_key"
            self.service = ReceiptService()

    def tearDown(self):
        self.repo_patcher.stop()
        self.ai_patcher.stop()

    @patch('src.services.receipt_service.Image.open')
    def test_extract_receipt_data_success(self, mock_img_open):
        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = '{"shop_name": "Test Store", "receipt_date": "2023-01-01", "total_amount": 50.0, "items": []}'
        self.service.model.generate_content.return_value = mock_response

        data = self.service.extract_receipt_data("fake_path.jpg")

        self.assertEqual(data['shop_name'], "Test Store")
        self.assertEqual(data['total_amount'], 50.0)
        self.service.model.generate_content.assert_called_once()

    @patch('src.services.receipt_service.Image.open')
    def test_extract_receipt_data_with_markdown(self, mock_img_open):
        # Mock Gemini response with markdown backticks
        mock_response = MagicMock()
        mock_response.text = '```json\n{"shop_name": "Markdown Store", "items": []}\n```'
        self.service.model.generate_content.return_value = mock_response

        data = self.service.extract_receipt_data("fake_path.jpg")

        self.assertEqual(data['shop_name'], "Markdown Store")

    def test_save_receipt_logic(self):
        receipt_data = {
            'shop_name': 'Costco',
            'receipt_date': '2023-05-01',
            'total_amount': 100.0,
            'image_path': 'receipts/test.jpg',
            'items': [
                {'item_name': 'Milk', 'quantity': 2, 'unit_price': 5.0}
            ]
        }
        
        self.mock_repo.create_receipt_with_items.return_value = 1
        
        receipt_id = self.service.save_receipt(receipt_data, user_id=1)
        
        self.assertEqual(receipt_id, 1)
        # Verify total_price was calculated for the item
        call_args = self.mock_repo.create_receipt_with_items.call_args[0]
        self.assertEqual(call_args[1][0]['total_price'], 10.0)

    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_ensure_upload_dir(self, mock_makedirs, mock_exists):
        mock_exists.return_value = False
        
        from config import Config
        path = self.service._ensure_upload_dir()
        
        self.assertTrue(path.endswith('receipts'))
        self.assertEqual(mock_makedirs.call_count, 2)

    def test_get_expenditure_summary(self):
        self.mock_repo.get_expenditure_summary.return_value = {'total_spent': 500.0}
        
        summary = self.service.get_expenditure_summary("2023-01-01", "2023-01-31")
        
        self.assertEqual(summary['total_spent'], 500.0)
        self.mock_repo.get_expenditure_summary.assert_called_once()


if __name__ == '__main__':
    unittest.main()
