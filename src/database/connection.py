"""Database connection pooling management."""
import logging
from contextlib import contextmanager
from typing import Optional
import psycopg2
from psycopg2 import pool
from config import Config

logger = logging.getLogger(__name__)


class DatabasePool:
    """Singleton database connection pool."""

    _instance: Optional['DatabasePool'] = None
    _pool: Optional[pool.ThreadedConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, minconn: int = None, maxconn: int = None):
        """
        Initialize the connection pool.

        Args:
            minconn: Minimum number of connections (default from Config)
            maxconn: Maximum number of connections (default from Config)
        """
        if self._pool is not None:
            logger.warning("Connection pool already initialized")
            return

        minconn = minconn or Config.DB_POOL_MIN
        maxconn = maxconn or Config.DB_POOL_MAX

        try:
            self._pool = pool.ThreadedConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD
            )
            logger.info(f"Database connection pool initialized (min={minconn}, max={maxconn})")
        except psycopg2.Error as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def get_connection(self):
        """
        Get a connection from the pool.

        Returns:
            psycopg2 connection object

        Raises:
            Exception if pool is not initialized or no connections available
        """
        if self._pool is None:
            raise Exception("Connection pool not initialized. Call initialize() first.")

        try:
            conn = self._pool.getconn()
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise

    def return_connection(self, conn):
        """
        Return a connection to the pool.

        Args:
            conn: psycopg2 connection object to return
        """
        if self._pool is None:
            logger.warning("Attempting to return connection to uninitialized pool")
            return

        try:
            self._pool.putconn(conn)
        except psycopg2.Error as e:
            logger.error(f"Failed to return connection to pool: {e}")
            raise

    def close_all(self):
        """Close all connections in the pool."""
        if self._pool is not None:
            self._pool.closeall()
            logger.info("All database connections closed")
            self._pool = None


# Global database pool instance
db_pool = DatabasePool()


@contextmanager
def get_db_connection():
    """
    Context manager for database connections with automatic commit/rollback.

    Usage:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM table")
                results = cur.fetchall()

    Yields:
        psycopg2 connection object

    The connection is automatically:
    - Committed if no exception occurs
    - Rolled back if an exception occurs
    - Returned to the pool when done
    """
    conn = db_pool.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction failed, rolling back: {e}")
        raise
    finally:
        db_pool.return_connection(conn)


@contextmanager
def get_db_cursor(commit=True):
    """
    Context manager for database cursor with connection management.

    Usage:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM table")
            results = cur.fetchall()

    Args:
        commit: Whether to commit on success (default True)

    Yields:
        psycopg2 cursor object
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
