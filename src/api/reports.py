"""Report API endpoints."""
from flask import Blueprint, request
from src.services.report_service import ReportService
from src.middleware.auth_middleware import require_auth, require_role
from src.utils.responses import success_response, error_response

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')
report_service = ReportService()


@reports_bp.route('/sales', methods=['GET'])
@require_auth
@require_role('admin')
def get_sales_report():
    """
    Get sales report by period (admin only).

    Headers:
        Authorization: Bearer <token>

    Query parameters:
        start_date: Start date (ISO format, optional, defaults to 30 days ago)
        end_date: End date (ISO format, optional, defaults to today)
        group_by: Grouping ("day", "week", "month", default "day")

    Returns:
        200: Sales report
        403: Forbidden (not admin)
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    group_by = request.args.get('group_by', 'day')

    if group_by not in ['day', 'week', 'month']:
        return error_response("group_by must be 'day', 'week', or 'month'", 400)

    report = report_service.get_sales_report(
        start_date=start_date,
        end_date=end_date,
        group_by=group_by
    )

    return success_response(report)


@reports_bp.route('/top-items', methods=['GET'])
@require_auth
@require_role('admin')
def get_top_items():
    """
    Get top selling items (admin only).

    Headers:
        Authorization: Bearer <token>

    Query parameters:
        start_date: Start date (ISO format, optional)
        end_date: End date (ISO format, optional)
        limit: Number of items (default 5)

    Returns:
        200: Top items report
        403: Forbidden (not admin)
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', 5, type=int)

    report = report_service.get_top_items_report(
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

    return success_response(report)


@reports_bp.route('/top-customers', methods=['GET'])
@require_auth
@require_role('admin')
def get_top_customers():
    """
    Get top customers by spending (admin only).

    Headers:
        Authorization: Bearer <token>

    Query parameters:
        start_date: Start date (ISO format, optional)
        end_date: End date (ISO format, optional)
        limit: Number of customers (default 5)

    Returns:
        200: Top customers report
        403: Forbidden (not admin)
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', 5, type=int)

    report = report_service.get_top_customers_report(
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

    return success_response(report)
