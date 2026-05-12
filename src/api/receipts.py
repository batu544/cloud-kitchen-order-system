"""Receipt API endpoints for operating expense management."""
import os
from datetime import datetime
from flask import Blueprint, request, g, send_from_directory
from src.services.receipt_service import ReceiptService
from src.middleware.auth_middleware import require_auth, require_role
from src.utils.responses import success_response, error_response
from config import Config

receipts_bp = Blueprint('receipts', __name__, url_prefix='/api/receipts')
receipt_service = ReceiptService()


@receipts_bp.route('/upload', methods=['POST'])
@require_auth
@require_role('staff', 'admin')
def upload_receipt():
    """
    Upload a receipt image and get AI-extracted data.
    """
    if 'file' not in request.files:
        return error_response("No file uploaded", 400)
    
    file = request.files['file']
    if file.filename == '':
        return error_response("No file selected", 400)

    try:
        extracted_data = receipt_service.process_receipt_upload(file, g.current_user['user_id'])
        return success_response(extracted_data)
    except Exception as e:
        return error_response(str(e), 500)


@receipts_bp.route('/confirm', methods=['POST'])
@require_auth
@require_role('staff', 'admin')
def confirm_receipt():
    """
    Save the confirmed receipt data after user review.
    """
    data = request.get_json()
    if not data:
        return error_response("Missing receipt data", 400)

    try:
        receipt_id = receipt_service.save_receipt(data, g.current_user['user_id'])
        return success_response({'receipt_id': receipt_id}, "Receipt saved successfully")
    except Exception as e:
        return error_response(str(e), 500)


@receipts_bp.route('/expenditure', methods=['GET'])
@require_auth
@require_role('admin')
def get_expenditure_report():
    """
    Get expenditure report for a period.
    """
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month

    expenditures = receipt_service.get_monthly_expenditure(year, month)
    summary = receipt_service.get_expenditure_summary(
        f"{year}-{month:02d}-01",
        f"{year}-{month:02d}-28" # Simple logic for now, summary uses full month in service
    )
    
    return success_response({
        'expenditures': expenditures,
        'summary': summary
    })


@receipts_bp.route('/images/<path:filename>')
@require_auth
def get_receipt_image(filename):
    """
    Serve uploaded receipt images.
    """
    receipts_dir = os.path.join(Config.UPLOAD_FOLDER, 'receipts')
    return send_from_directory(receipts_dir, filename)


@receipts_bp.route('/<int:receipt_id>', methods=['GET'])
@require_auth
@require_role('staff', 'admin')
def get_receipt_details(receipt_id):
    """Get full receipt details with items."""
    receipt = receipt_service.get_receipt(receipt_id)
    if not receipt:
        return error_response("Receipt not found", 404)
    return success_response(receipt)
