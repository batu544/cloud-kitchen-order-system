"""Database migration runner."""
import os
import logging
from pathlib import Path
import psycopg2
from src.database.connection import get_db_connection

logger = logging.getLogger(__name__)

# Get migrations directory path
MIGRATIONS_DIR = Path(__file__).parent.parent.parent / 'migrations'


def get_migration_files():
    """
    Get all SQL migration files in order.

    Returns:
        List of tuples (version, filepath, description)
    """
    if not MIGRATIONS_DIR.exists():
        logger.error(f"Migrations directory not found: {MIGRATIONS_DIR}")
        return []

    migrations = []
    for filepath in sorted(MIGRATIONS_DIR.glob('*.sql')):
        filename = filepath.name
        # Extract version from filename (e.g., 001_create_base_tables.sql)
        try:
            version_str = filename.split('_')[0]
            version = int(version_str)
            description = filename.replace(version_str + '_', '').replace('.sql', '').replace('_', ' ')
            migrations.append((version, filepath, description))
        except (ValueError, IndexError):
            logger.warning(f"Skipping invalid migration filename: {filename}")
            continue

    return migrations


def get_applied_migrations(cursor):
    """
    Get list of already applied migration versions.

    Args:
        cursor: Database cursor

    Returns:
        Set of applied version numbers
    """
    try:
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        return {row[0] for row in cursor.fetchall()}
    except psycopg2.Error:
        # schema_migrations table doesn't exist yet
        return set()


def apply_migration(cursor, version, filepath, description):
    """
    Apply a single migration file.

    Args:
        cursor: Database cursor
        version: Migration version number
        filepath: Path to SQL file
        description: Migration description

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Applying migration {version}: {description}")

        # Read and execute the SQL file
        with open(filepath, 'r') as f:
            sql = f.read()

        cursor.execute(sql)

        # Record the migration
        cursor.execute(
            """
            INSERT INTO schema_migrations (version, description, applied_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (version) DO NOTHING
            """,
            (version, description)
        )

        logger.info(f"Migration {version} applied successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to apply migration {version}: {e}")
        raise


def run_migrations():
    """
    Run all pending migrations.

    Returns:
        Number of migrations applied
    """
    logger.info("Starting database migrations")

    migration_files = get_migration_files()
    if not migration_files:
        logger.warning("No migration files found")
        return 0

    applied_count = 0

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get already applied migrations
                applied_versions = get_applied_migrations(cursor)
                logger.info(f"Found {len(applied_versions)} already applied migrations")

                # Apply pending migrations
                for version, filepath, description in migration_files:
                    if version in applied_versions:
                        logger.debug(f"Migration {version} already applied, skipping")
                        continue

                    apply_migration(cursor, version, filepath, description)
                    applied_count += 1

                conn.commit()

        logger.info(f"Migrations complete. Applied {applied_count} new migration(s)")
        return applied_count

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def get_migration_status():
    """
    Get status of all migrations.

    Returns:
        List of tuples (version, description, applied_at or None)
    """
    migration_files = get_migration_files()
    status = []

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                applied_versions = get_applied_migrations(cursor)

                # Get applied dates
                cursor.execute("SELECT version, applied_at FROM schema_migrations")
                applied_dates = {row[0]: row[1] for row in cursor.fetchall()}

                for version, filepath, description in migration_files:
                    applied_at = applied_dates.get(version)
                    status.append((version, description, applied_at))

        return status

    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")
        return []


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # Initialize database pool
    from src.database.connection import db_pool
    db_pool.initialize()

    # Run migrations
    try:
        count = run_migrations()
        print(f"\nMigrations complete! Applied {count} new migration(s).")

        # Show status
        print("\nMigration Status:")
        print("-" * 80)
        for version, description, applied_at in get_migration_status():
            status = f"Applied: {applied_at}" if applied_at else "Pending"
            print(f"{version:03d} | {description:40s} | {status}")

    except Exception as e:
        print(f"\nMigration failed: {e}")
        exit(1)
