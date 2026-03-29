"""Order service for order creation and management (SPEC.md lines 54-89)."""
import secrets
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List, Tuple
from src.repositories.order_repository import OrderRepository
from src.repositories.customer_repository import CustomerRepository
from src.repositories.menu_repository import MenuRepository
from src.services.pricing_service import (
    calculate_line_total,
    apply_discount,
    calculate_order_total
)
from src.utils.validators import validate_phone, validate_order_items, validate_discount


class OrderService:
    """Service for order operations."""

    def __init__(self):
        self.order_repo = OrderRepository()
        self.customer_repo = CustomerRepository()
        self.menu_repo = MenuRepository()

    def _generate_order_ref(self) -> str:
        """
        Generate unique order reference.

        Returns:
            Order reference string (e.g., ORD-20240328-ABC123)
        """
        date_str = datetime.now().strftime('%Y%m%d')
        random_str = secrets.token_hex(3).upper()
        return f"ORD-{date_str}-{random_str}"

    def lookup_customer_by_phone(self, phone: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Staff helper: find existing customer by phone (SPEC.md line 26).

        Args:
            phone: Phone number

        Returns:
            Tuple of (found, message, customer_data)
        """
        # Validate phone
        is_valid, phone_result = validate_phone(phone)
        if not is_valid:
            return False, phone_result, None

        normalized_phone = phone_result

        # Look up customer
        customer = self.customer_repo.find_by_phone(normalized_phone)

        if customer:
            # Get order count
            order_history = self.customer_repo.get_customer_order_history(
                customer['cust_id'], limit=100
            )
            customer['order_history_count'] = len(order_history)
            return True, "Customer found", customer
        else:
            return False, "Customer not found", None

    def create_order(self, order_request: Dict, placed_by_user_id: int = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Main order creation logic (SPEC.md lines 54-89).

        Process:
        1. Validate customer (lookup by phone if staff order per SPEC.md line 26)
        2. Fetch menu items and validate availability
        3. Calculate line totals (including catering)
        4. Calculate subtotal
        5. Apply discount (if provided)
        6. Calculate total
        7. Create order and order_items in transaction
        8. Create initial status history entry
        9. Generate order_ref
        10. Return order details

        Args:
            order_request: Order data with customer info, items, discount, tip
            placed_by_user_id: Optional user ID placing the order

        Returns:
            Tuple of (success, message, order_data)
        """
        # Extract data
        customer_data = order_request.get('customer', {})
        items_data = order_request.get('items', [])
        discount = order_request.get('discount')
        tip_amount = Decimal(str(order_request.get('tip_amount', 0)))
        notes = order_request.get('notes')

        # Validate items
        item_errors = validate_order_items(items_data)
        if item_errors:
            return False, '; '.join(item_errors), None

        # Validate and normalize phone
        phone = customer_data.get('phone')
        is_valid_phone, phone_result = validate_phone(phone)
        if not is_valid_phone:
            return False, phone_result, None

        normalized_phone = phone_result

        # Handle customer lookup/creation
        cust_id = customer_data.get('cust_id')

        if not cust_id:
            # Try to find existing customer by phone
            existing_customer = self.customer_repo.find_by_phone(normalized_phone)

            if existing_customer:
                cust_id = existing_customer['cust_id']
            elif customer_data.get('name'):
                # Create new customer for registered users
                cust_id = self.customer_repo.create_customer(
                    name=customer_data['name'],
                    phone=normalized_phone,
                    email=customer_data.get('email'),
                    address=customer_data.get('address')
                )

        # Get menu items
        item_ids = [item['kic_id'] for item in items_data]
        menu_items = self.menu_repo.get_items_by_ids(item_ids)

        if len(menu_items) != len(set(item_ids)):
            return False, "One or more menu items not found", None

        # Create menu items lookup
        menu_items_map = {item['kic_id']: item for item in menu_items}

        # Calculate line totals
        order_items = []
        subtotal = Decimal('0')

        for item_data in items_data:
            kic_id = item_data['kic_id']
            menu_item = menu_items_map.get(kic_id)

            if not menu_item:
                return False, f"Menu item {kic_id} not found", None

            if not menu_item.get('is_active', False):
                return False, f"Menu item '{menu_item['kic_name']}' is not available", None

            quantity = item_data.get('quantity', 1)
            unit_price = Decimal(str(menu_item['kic_price']))
            is_catering = item_data.get('is_catering', False) or menu_item.get('is_catering', False)
            catering_size = item_data.get('catering_size')

            # Calculate line total
            line_total = calculate_line_total(
                unit_price=unit_price,
                quantity=quantity,
                is_catering=is_catering,
                catering_size=catering_size
            )

            order_item = {
                'kic_id': kic_id,
                'name': menu_item['kic_name'],
                'unit_price': unit_price,
                'quantity': quantity,
                'special_instructions': item_data.get('special_instructions'),
                'is_catering': is_catering,
                'catering_size': catering_size,
                'line_total': line_total
            }

            order_items.append(order_item)
            subtotal += line_total

        # Apply discount
        discount_amount = Decimal('0')
        discount_type = None

        if discount:
            discount_type = discount.get('type')
            discount_value = Decimal(str(discount.get('value', 0)))

            # Validate discount
            discount_errors = validate_discount(discount_type, float(discount_value))
            if discount_errors:
                return False, '; '.join(discount_errors), None

            discount_amount = apply_discount(subtotal, discount_type, discount_value)

        # Calculate final total (no tax per user requirement)
        tax_amount, total_amount = calculate_order_total(
            subtotal=subtotal,
            discount_amount=discount_amount,
            tip_amount=tip_amount
        )

        # Get default status (Pending)
        statuses = self.order_repo.get_all_statuses()
        pending_status = next((s for s in statuses if s['status_name'] == 'Pending'), None)
        status_id = pending_status['status_id'] if pending_status else 1

        # Create order data
        order_data = {
            'order_ref': self._generate_order_ref(),
            'cust_id': cust_id,
            'order_phone': normalized_phone,
            'placed_by_user_id': placed_by_user_id,
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'discount_type': discount_type,
            'tip_amount': tip_amount,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'payment_status': 'pending',
            'current_status_id': status_id,
            'notes': notes
        }

        # Create order with items in transaction
        try:
            order_id = self.order_repo.create_order_with_items(order_data, order_items)

            if not order_id:
                return False, "Failed to create order", None

            # Fetch created order
            created_order = self.order_repo.get_order_with_items(order_id)

            return True, "Order created successfully", created_order

        except Exception as e:
            return False, f"Failed to create order: {str(e)}", None

    def get_order(self, order_id: int, user_id: int = None, user_role: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get order details with authorization check.

        Args:
            order_id: Order ID
            user_id: Optional user ID for authorization
            user_role: Optional user role

        Returns:
            Tuple of (success, message, order_data)
        """
        order = self.order_repo.get_order_with_items(order_id)

        if not order:
            return False, "Order not found", None

        # Authorization check
        if user_id and user_role not in ['staff', 'admin']:
            # Regular users can only see their own orders
            if order.get('placed_by_user_id') != user_id:
                return False, "Unauthorized", None

        # Get status history
        status_history = self.order_repo.get_order_status_history(order_id)
        order['status_history'] = status_history

        return True, "Order found", order

    def track_order(self, order_ref: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Public order tracking by order reference.

        Args:
            order_ref: Order reference string

        Returns:
            Tuple of (success, message, order_data)
        """
        order = self.order_repo.find_by_order_ref(order_ref)

        if not order:
            return False, "Order not found", None

        # Get status history
        status_history = self.order_repo.get_order_status_history(order['order_id'])
        order['status_history'] = status_history

        return True, "Order found", order

    def update_order_status(self, order_id: int, status_id: int,
                           changed_by_user_id: int = None, note: str = None) -> Tuple[bool, str]:
        """
        Update order status (staff only).

        Args:
            order_id: Order ID
            status_id: New status ID
            changed_by_user_id: User making the change
            note: Optional note

        Returns:
            Tuple of (success, message)
        """
        success = self.order_repo.update_order_status(
            order_id, status_id, changed_by_user_id, note
        )

        if success:
            return True, "Order status updated"
        else:
            return False, "Failed to update order status"

    def get_customer_orders(self, cust_id: int) -> List[Dict]:
        """
        Get orders for a customer.

        Args:
            cust_id: Customer ID

        Returns:
            List of orders
        """
        return self.order_repo.get_orders_by_customer(cust_id)

    def get_recent_orders(self, limit: int = 50) -> List[Dict]:
        """
        Get recent orders (staff/admin).

        Args:
            limit: Maximum orders to return

        Returns:
            List of orders
        """
        return self.order_repo.get_recent_orders(limit)
