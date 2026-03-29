"""Seed data for development and testing."""
import logging
from decimal import Decimal
from src.database.connection import get_db_connection
from src.utils.security import hash_password

logger = logging.getLogger(__name__)


def load_seed_data():
    """Load sample data into the database."""
    logger.info("Loading seed data...")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Sample menu items
                menu_items = [
                    ('Chicken Tikka Masala', Decimal('12.99'), 2, 'Classic Indian curry', False),
                    ('Paneer Butter Masala', Decimal('11.99'), 2, 'Cottage cheese in creamy tomato sauce', False),
                    ('Biryani', Decimal('13.99'), 2, 'Fragrant rice with spices', False),
                    ('Samosa', Decimal('3.99'), 1, 'Crispy pastry with spiced filling', False),
                    ('Naan Bread', Decimal('2.99'), 1, 'Fresh baked flatbread', False),
                    ('Gulab Jamun', Decimal('4.99'), 3, 'Sweet milk dumplings', False),
                    ('Mango Lassi', Decimal('3.99'), 4, 'Refreshing yogurt drink', False),
                    ('Party Tray - Chicken', Decimal('15.00'), 5, 'Catering tray', True),
                    ('Party Tray - Vegetarian', Decimal('12.00'), 5, 'Catering tray', True),
                ]

                for name, price, category_id, desc, is_catering in menu_items:
                    cursor.execute(
                        """
                        INSERT INTO kitch_item_catalg (kic_name, kic_price, category_id, description, is_catering, is_active)
                        VALUES (%s, %s, %s, %s, %s, TRUE)
                        ON CONFLICT DO NOTHING
                        """,
                        (name, price, category_id, desc, is_catering)
                    )

                logger.info("Sample menu items added")

                # Sample customers
                customers = [
                    ('John Doe', '5551234567', 'john@example.com', '123 Main St'),
                    ('Jane Smith', '5559876543', 'jane@example.com', '456 Oak Ave'),
                    ('Bob Wilson', '5555555555', 'bob@example.com', '789 Pine Rd'),
                ]

                for name, phone, email, address in customers:
                    cursor.execute(
                        """
                        INSERT INTO kitch_customer (cust_name, cust_phone_number, cust_email, cust_address)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (cust_phone_number) DO NOTHING
                        RETURNING cust_id
                        """,
                        (name, phone, email, address)
                    )

                logger.info("Sample customers added")

                # Sample users (staff and admin)
                # Password for all: "password123"
                hashed_pw = hash_password("password123")

                users = [
                    ('admin@kitchen.com', hashed_pw, 'admin', None),
                    ('staff@kitchen.com', hashed_pw, 'staff', None),
                    ('john@example.com', hashed_pw, 'customer', 1),
                ]

                for username, password_hash, role, cust_id in users:
                    cursor.execute(
                        """
                        INSERT INTO kitch_user (username, password_hash, role, cust_id)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (username) DO NOTHING
                        """,
                        (username, password_hash, role, cust_id)
                    )

                logger.info("Sample users added")

            conn.commit()

        logger.info("Seed data loaded successfully")
        print("\nSample Users Created:")
        print("-" * 60)
        print("Username: admin@kitchen.com | Password: password123 | Role: admin")
        print("Username: staff@kitchen.com | Password: password123 | Role: staff")
        print("Username: john@example.com  | Password: password123 | Role: customer")

    except Exception as e:
        logger.error(f"Failed to load seed data: {e}")
        raise


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    from src.database.connection import db_pool
    db_pool.initialize()

    load_seed_data()
