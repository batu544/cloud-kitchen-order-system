#!/usr/bin/env python3
"""Cloud Kitchen Order System - Application Entry Point."""
import logging
from src import create_app
from src.database.connection import db_pool
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if Config.DEBUG else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    try:
        # Initialize database connection pool
        logger.info("Initializing database connection pool...")
        db_pool.initialize()

        # Create Flask application
        logger.info("Creating Flask application...")
        app = create_app()

        # Display startup information
        print("=" * 70)
        print("Cloud Kitchen Order System")
        print("=" * 70)
        print(f"Environment: {Config.ENV}")
        print(f"Debug Mode: {Config.DEBUG}")
        print(f"Server: http://{Config.HOST}:{Config.PORT}")
        print(f"API Base: http://{Config.HOST}:{Config.PORT}/api")
        print("=" * 70)
        print("\nPress CTRL+C to stop the server\n")

        # Run the application
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            threaded=True
        )

    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
        db_pool.close_all()
        print("\nServer stopped.")

    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        db_pool.close_all()
        exit(1)


if __name__ == '__main__':
    main()
