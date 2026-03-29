"""Global error handling for Flask application."""
import logging
from flask import Flask
from psycopg2 import IntegrityError, OperationalError
from src.utils.responses import error_response

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask):
    """
    Register global error handlers for the Flask application.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(400)
    def bad_request(e):
        """Handle 400 Bad Request errors."""
        return error_response("Bad request", 400)

    @app.errorhandler(401)
    def unauthorized(e):
        """Handle 401 Unauthorized errors."""
        return error_response("Unauthorized", 401)

    @app.errorhandler(403)
    def forbidden(e):
        """Handle 403 Forbidden errors."""
        return error_response("Forbidden", 403)

    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 Not Found errors."""
        return error_response("Resource not found", 404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        """Handle 405 Method Not Allowed errors."""
        return error_response("Method not allowed", 405)

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        """Handle database integrity constraint violations."""
        logger.error(f"Database integrity error: {e}")
        message = "Database constraint violation"

        error_str = str(e).lower()
        if 'unique' in error_str:
            message = "A record with this value already exists"
        elif 'foreign key' in error_str:
            message = "Referenced record does not exist"
        elif 'not null' in error_str:
            message = "Required field is missing"

        return error_response(message, 409)

    @app.errorhandler(OperationalError)
    def handle_operational_error(e):
        """Handle database operational errors."""
        logger.error(f"Database operational error: {e}")
        return error_response("Database connection error", 503)

    @app.errorhandler(ValueError)
    def handle_value_error(e):
        """Handle value errors from business logic."""
        logger.warning(f"Value error: {e}")
        return error_response(str(e), 400)

    @app.errorhandler(Exception)
    def handle_generic_error(e):
        """Handle all other unhandled exceptions."""
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return error_response("Internal server error", 500)
