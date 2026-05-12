"""Service for managing receipts and extracting data using AI."""
import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from werkzeug.utils import secure_filename
from PIL import Image
import google.generativeai as genai

from config import Config
from src.repositories.receipt_repository import ReceiptRepository

logger = logging.getLogger(__name__)

class ReceiptService:
    """Service for receipt management operations."""

    def __init__(self):
        self.receipt_repo = ReceiptRepository()
        if Config.GOOGLE_API_KEY:
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("GOOGLE_API_KEY not set. Receipt extraction will be unavailable.")

    def _ensure_upload_dir(self):
        """Ensure the upload directory exists."""
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)
        
        receipts_dir = os.path.join(Config.UPLOAD_FOLDER, 'receipts')
        if not os.path.exists(receipts_dir):
            os.makedirs(receipts_dir)
        return receipts_dir

    def extract_receipt_data(self, image_path: str) -> Dict:
        """
        Extract data from a receipt image using Gemini Vision.
        """
        if not self.model:
            raise ValueError("AI extraction is unavailable (API key missing).")

        img = Image.open(image_path)
        
        prompt = """
        Analyze this receipt and extract the following information in JSON format:
        - shop_name: The name of the store or restaurant.
        - receipt_date: The date of purchase in YYYY-MM-DD format.
        - total_amount: The final total amount paid (numeric).
        - items: A list of objects, each containing:
            - item_name: Name of the item.
            - quantity: Quantity purchased (numeric).
            - unit_price: Price per unit (numeric).
            - total_price: Total for this line item (numeric).

        If you cannot find a specific field, return null for it.
        Only return the JSON object, no other text.
        """

        response = self.model.generate_content([prompt, img])
        
        try:
            # Clean up the response text if it contains markdown code blocks
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
            
            return json.loads(text)
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"Raw response: {response.text}")
            raise ValueError("Failed to extract data from receipt accurately.")

    def process_receipt_upload(self, file, user_id: int) -> Dict:
        """
        Save the uploaded file and return extracted data for review.
        """
        receipts_dir = self._ensure_upload_dir()
        
        # Generate a unique filename to avoid collisions
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(receipts_dir, filename)
        
        file.save(filepath)
        
        # Relative path for storage in DB
        db_image_path = os.path.join('receipts', filename)
        
        try:
            extracted_data = self.extract_receipt_data(filepath)
            extracted_data['image_path'] = db_image_path
            return extracted_data
        except Exception as e:
            # Still return the image path so user can fill data manually if AI fails
            return {
                'shop_name': None,
                'receipt_date': datetime.now().strftime('%Y-%m-%d'),
                'total_amount': 0.0,
                'items': [],
                'image_path': db_image_path,
                'error': str(e)
            }

    def save_receipt(self, data: Dict, user_id: int) -> int:
        """
        Save the confirmed receipt data to the database.
        """
        receipt_data = {
            'shop_name': data.get('shop_name'),
            'receipt_date': data.get('receipt_date'),
            'total_amount': data.get('total_amount', 0),
            'image_path': data.get('image_path'),
            'uploaded_by': user_id,
            'raw_data': json.dumps(data)
        }
        
        items = data.get('items', [])
        # Ensure items have the required total_price if missing
        for item in items:
            if 'total_price' not in item or item['total_price'] is None:
                qty = item.get('quantity') or 1
                price = item.get('unit_price') or 0
                item['total_price'] = float(qty) * float(price)

        return self.receipt_repo.create_receipt_with_items(receipt_data, items)

    def get_receipt(self, receipt_id: int) -> Optional[Dict]:
        """Get a receipt by ID."""
        return self.receipt_repo.get_receipt_with_items(receipt_id)

    def get_monthly_expenditure(self, year: int, month: int) -> List[Dict]:
        """Get expenditure report for a month."""
        return self.receipt_repo.get_monthly_expenditure(year, month)

    def get_expenditure_summary(self, start_date: str, end_date: str) -> Dict:
        """Get summary stats for expenditure."""
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59)
        return self.receipt_repo.get_expenditure_summary(start, end)
