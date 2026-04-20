"""Flask application factory."""
import logging
import datetime
from decimal import Decimal
from flask import Flask
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config

limiter = Limiter(key_func=get_remote_address, default_limits=[])
from src.middleware.error_handler import register_error_handlers  # noqa: E402
from src.api.auth import auth_bp  # noqa: E402
from src.api.menu import menu_bp  # noqa: E402
from src.api.orders import orders_bp  # noqa: E402
from src.api.payments import payments_bp  # noqa: E402
from src.api.reports import reports_bp  # noqa: E402
from src.api.admin import admin_bp  # noqa: E402
from src.api.web_routes import web_bp  # noqa: E402


class CustomJSONProvider(DefaultJSONProvider):
    """JSON provider that handles datetime and Decimal types."""

    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """
    Flask application factory.

    Args:
        config_class: Configuration class to use

    Returns:
        Configured Flask application
    """
    # Initialize Flask app
    app = Flask(__name__,
                static_folder='web/static',
                template_folder='web/templates')
    app.json_provider_class = CustomJSONProvider
    app.json = CustomJSONProvider(app)

    # Load configuration
    app.config.from_object(config_class)

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if app.config['DEBUG'] else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    logger.info(f"Starting Cloud Kitchen Order System in {config_class.ENV} mode")

    # Initialize CORS for API access (wildcard kept — local Wi-Fi deployment)
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Initialize rate limiter
    limiter.init_app(app)

    # Security headers on every response
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' cdn.tailwindcss.com cdn.jsdelivr.net"
        )
        return response

    # Register error handlers
    register_error_handlers(app)

    # Register API blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    # Register web UI blueprint
    app.register_blueprint(web_bp)

    logger.info("All blueprints registered")

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return {
            'status': 'healthy',
            'service': 'Cloud Kitchen Order System',
            'version': '1.0.0'
        }

    # Debug-only: reset rate limiter storage (for E2E test isolation)
    if app.config.get('DEBUG'):
        @app.route('/debug/reset-limits', methods=['POST'])
        def reset_limits():
            limiter.reset()
            return {'status': 'ok'}

    return app
