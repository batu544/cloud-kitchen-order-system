"""Flask application factory."""
import logging
from flask import Flask
from flask_cors import CORS
from config import Config
from src.middleware.error_handler import register_error_handlers
from src.api.auth import auth_bp
from src.api.menu import menu_bp
from src.api.orders import orders_bp
from src.api.payments import payments_bp
from src.api.reports import reports_bp
from src.api.web_routes import web_bp

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

    # Load configuration
    app.config.from_object(config_class)

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if app.config['DEBUG'] else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    logger.info(f"Starting Cloud Kitchen Order System in {config_class.ENV} mode")

    # Initialize CORS for API access
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Register error handlers
    register_error_handlers(app)

    # Register API blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(reports_bp)

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

    return app
