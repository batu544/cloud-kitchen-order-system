"""Application configuration management."""
import os
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""

    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    ENV = os.getenv('FLASK_ENV', 'development')

    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME', 'kitchen_db')
    DB_USER = os.getenv('DB_USER', 'kitchen_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Database Connection Pool
    DB_POOL_MIN = int(os.getenv('DB_POOL_MIN', 2))
    DB_POOL_MAX = int(os.getenv('DB_POOL_MAX', 10))

    # JWT Configuration
    _jwt_secret = os.getenv('JWT_SECRET_KEY')
    if not _jwt_secret:
        import warnings
        warnings.warn(
            "JWT_SECRET_KEY not set in environment — falling back to SECRET_KEY. "
            "Set JWT_SECRET_KEY explicitly in production.",
            stacklevel=2
        )
        _jwt_secret = SECRET_KEY
    JWT_SECRET_KEY = _jwt_secret
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))

    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))

    # Business Configuration
    TAX_RATE = Decimal(os.getenv('TAX_RATE', '0.00'))

    @classmethod
    def get_db_connection_string(cls):
        """Get PostgreSQL connection string."""
        return (
            f"host={cls.DB_HOST} "
            f"port={cls.DB_PORT} "
            f"dbname={cls.DB_NAME} "
            f"user={cls.DB_USER} "
            f"password={cls.DB_PASSWORD}"
        )


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    DB_NAME = 'kitchen_db_test'
    DEBUG = False
