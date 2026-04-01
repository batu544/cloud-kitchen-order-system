"""Unit tests for order_service.py — validation and calculation logic with mocked repos."""
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch


def make_menu_item(kic_id=1, name='Curry', price=10.00, is_catering=False, is_active=True):
    return {
        'kic_id': kic_id,
        'kic_name': name,
        'kic_price': price,
        'is_catering': is_catering,
        'is_active': is_active,
    }


class TestLookupCustomerByPhone(unittest.TestCase):

    def setUp(self):
        self.order_repo_patcher = patch('src.services.order_service.OrderRepository')
        self.cust_repo_patcher = patch('src.services.order_service.CustomerRepository')
        self.menu_repo_patcher = patch('src.services.order_service.MenuRepository')

        self.order_repo_patcher.start()
        self.MockCustRepo = self.cust_repo_patcher.start()
        self.menu_repo_patcher.start()

        self.mock_cust_repo = MagicMock()
        self.MockCustRepo.return_value = self.mock_cust_repo

        from src.services.order_service import OrderService
        self.service = OrderService()

    def tearDown(self):
        self.order_repo_patcher.stop()
        self.cust_repo_patcher.stop()
        self.menu_repo_patcher.stop()

    def test_found_customer(self):
        self.mock_cust_repo.find_by_phone.return_value = {'cust_id': 1, 'cust_name': 'Alice'}
        self.mock_cust_repo.get_customer_order_history.return_value = [{}, {}]

        ok, msg, data = self.service.lookup_customer_by_phone('1234567890')

        self.assertTrue(ok)
        self.assertEqual(data['cust_id'], 1)
        self.assertEqual(data['order_history_count'], 2)

    def test_not_found(self):
        self.mock_cust_repo.find_by_phone.return_value = None

        ok, msg, data = self.service.lookup_customer_by_phone('1234567890')

        self.assertFalse(ok)
        self.assertIsNone(data)

    def test_invalid_phone_format(self):
        ok, msg, data = self.service.lookup_customer_by_phone('123')

        self.assertFalse(ok)
        self.assertIsNone(data)
        self.mock_cust_repo.find_by_phone.assert_not_called()


class TestCreateOrderValidation(unittest.TestCase):

    def setUp(self):
        self.order_repo_patcher = patch('src.services.order_service.OrderRepository')
        self.cust_repo_patcher = patch('src.services.order_service.CustomerRepository')
        self.menu_repo_patcher = patch('src.services.order_service.MenuRepository')

        self.MockOrderRepo = self.order_repo_patcher.start()
        self.MockCustRepo = self.cust_repo_patcher.start()
        self.MockMenuRepo = self.menu_repo_patcher.start()

        self.mock_order_repo = MagicMock()
        self.mock_cust_repo = MagicMock()
        self.mock_menu_repo = MagicMock()
        self.MockOrderRepo.return_value = self.mock_order_repo
        self.MockCustRepo.return_value = self.mock_cust_repo
        self.MockMenuRepo.return_value = self.mock_menu_repo

        from src.services.order_service import OrderService
        self.service = OrderService()

    def tearDown(self):
        self.order_repo_patcher.stop()
        self.cust_repo_patcher.stop()
        self.menu_repo_patcher.stop()

    def _base_request(self, items=None, phone='1234567890'):
        return {
            'customer': {'phone': phone},
            'items': items or [{'kic_id': 1, 'quantity': 1}],
        }

    def test_empty_items_rejected(self):
        req = self._base_request(items=[])
        ok, msg, data = self.service.create_order(req)

        self.assertFalse(ok)
        self.assertIsNone(data)

    def test_missing_items_key(self):
        ok, msg, data = self.service.create_order({'customer': {'phone': '1234567890'}})

        self.assertFalse(ok)
        self.assertIsNone(data)

    def test_invalid_phone(self):
        req = self._base_request(phone='123')
        ok, msg, data = self.service.create_order(req)

        self.assertFalse(ok)
        self.assertIsNone(data)

    def test_item_not_in_catalog(self):
        self.mock_cust_repo.find_by_phone.return_value = None
        self.mock_menu_repo.get_items_by_ids.return_value = []  # nothing found

        req = self._base_request(items=[{'kic_id': 999, 'quantity': 1}])
        ok, msg, data = self.service.create_order(req)

        self.assertFalse(ok)
        self.assertIsNone(data)

    def test_invalid_discount_type(self):
        self.mock_cust_repo.find_by_phone.return_value = None
        item = make_menu_item()
        self.mock_menu_repo.get_items_by_ids.return_value = [item]

        req = self._base_request()
        req['discount'] = {'type': 'invalid', 'value': 10}

        ok, msg, data = self.service.create_order(req)

        self.assertFalse(ok)
        self.assertIsNone(data)

    def test_percent_discount_over_100_rejected(self):
        self.mock_cust_repo.find_by_phone.return_value = None
        item = make_menu_item()
        self.mock_menu_repo.get_items_by_ids.return_value = [item]

        req = self._base_request()
        req['discount'] = {'type': 'percent', 'value': 110}

        ok, msg, data = self.service.create_order(req)

        self.assertFalse(ok)
        self.assertIsNone(data)

    def test_inactive_item_rejected(self):
        self.mock_cust_repo.find_by_phone.return_value = None
        item = make_menu_item(is_active=False)
        self.mock_menu_repo.get_items_by_ids.return_value = [item]

        req = self._base_request()
        ok, msg, data = self.service.create_order(req)

        self.assertFalse(ok)
        self.assertIsNone(data)


class TestCreateOrderCalculations(unittest.TestCase):

    def setUp(self):
        self.order_repo_patcher = patch('src.services.order_service.OrderRepository')
        self.cust_repo_patcher = patch('src.services.order_service.CustomerRepository')
        self.menu_repo_patcher = patch('src.services.order_service.MenuRepository')

        self.MockOrderRepo = self.order_repo_patcher.start()
        self.MockCustRepo = self.cust_repo_patcher.start()
        self.MockMenuRepo = self.menu_repo_patcher.start()

        self.mock_order_repo = MagicMock()
        self.mock_cust_repo = MagicMock()
        self.mock_menu_repo = MagicMock()
        self.MockOrderRepo.return_value = self.mock_order_repo
        self.MockCustRepo.return_value = self.mock_cust_repo
        self.MockMenuRepo.return_value = self.mock_menu_repo

        # Default repo behaviour for successful order creation
        self.mock_cust_repo.find_by_phone.return_value = None
        self.mock_order_repo.get_all_statuses.return_value = [
            {'status_id': 1, 'status_name': 'Pending'}
        ]
        self.mock_order_repo.create_order_with_items.return_value = 100
        self.mock_order_repo.get_order_with_items.return_value = {
            'order_id': 100,
            'order_ref': 'ORD-TEST',
            'items': [],
            'status_history': [],
        }

        from src.services.order_service import OrderService
        self.service = OrderService()

    def tearDown(self):
        self.order_repo_patcher.stop()
        self.cust_repo_patcher.stop()
        self.menu_repo_patcher.stop()

    def _make_request(self, items_data, discount=None, tip=0):
        req = {
            'customer': {'phone': '1234567890'},
            'items': items_data,
            'tip_amount': tip,
        }
        if discount:
            req['discount'] = discount
        return req

    def test_subtotal_calculated_from_items(self):
        self.mock_menu_repo.get_items_by_ids.return_value = [
            make_menu_item(kic_id=1, price=10.00),
            make_menu_item(kic_id=2, price=20.00),
        ]

        items_data = [
            {'kic_id': 1, 'quantity': 2},  # 20.00
            {'kic_id': 2, 'quantity': 1},  # 20.00
        ]
        req = self._make_request(items_data)
        ok, msg, data = self.service.create_order(req)

        self.assertTrue(ok, msg)
        call_args = self.mock_order_repo.create_order_with_items.call_args
        order_data = call_args[0][0]
        self.assertEqual(order_data['subtotal'], Decimal('40.00'))

    def test_percent_discount_applied(self):
        self.mock_menu_repo.get_items_by_ids.return_value = [
            make_menu_item(kic_id=1, price=100.00),
        ]

        req = self._make_request(
            items_data=[{'kic_id': 1, 'quantity': 1}],
            discount={'type': 'percent', 'value': 10}
        )
        ok, msg, data = self.service.create_order(req)

        self.assertTrue(ok, msg)
        call_args = self.mock_order_repo.create_order_with_items.call_args
        order_data = call_args[0][0]
        self.assertEqual(order_data['total_amount'], Decimal('90.00'))  # 100 - 10%

    def test_fixed_discount_applied(self):
        self.mock_menu_repo.get_items_by_ids.return_value = [
            make_menu_item(kic_id=1, price=100.00),
        ]

        req = self._make_request(
            items_data=[{'kic_id': 1, 'quantity': 1}],
            discount={'type': 'fixed', 'value': 15}
        )
        ok, msg, data = self.service.create_order(req)

        self.assertTrue(ok, msg)
        call_args = self.mock_order_repo.create_order_with_items.call_args
        order_data = call_args[0][0]
        self.assertEqual(order_data['total_amount'], Decimal('85.00'))

    def test_tip_added_to_total(self):
        self.mock_menu_repo.get_items_by_ids.return_value = [
            make_menu_item(kic_id=1, price=100.00),
        ]

        req = self._make_request(
            items_data=[{'kic_id': 1, 'quantity': 1}],
            tip=5.00
        )
        ok, msg, data = self.service.create_order(req)

        self.assertTrue(ok, msg)
        call_args = self.mock_order_repo.create_order_with_items.call_args
        order_data = call_args[0][0]
        self.assertEqual(order_data['total_amount'], Decimal('105.00'))

    def test_catering_small_pricing(self):
        self.mock_menu_repo.get_items_by_ids.return_value = [
            make_menu_item(kic_id=1, price=10.00, is_catering=True),
        ]

        req = self._make_request(
            items_data=[{'kic_id': 1, 'quantity': 1, 'is_catering': True, 'catering_size': 'small'}]
        )
        ok, msg, data = self.service.create_order(req)

        self.assertTrue(ok, msg)
        call_args = self.mock_order_repo.create_order_with_items.call_args
        order_data = call_args[0][0]
        self.assertEqual(order_data['subtotal'], Decimal('36.00'))  # 10 * 4 * 0.9

    def test_customer_linked_by_phone(self):
        self.mock_cust_repo.find_by_phone.return_value = {'cust_id': 7}
        self.mock_menu_repo.get_items_by_ids.return_value = [
            make_menu_item(kic_id=1, price=10.00),
        ]

        req = self._make_request(items_data=[{'kic_id': 1, 'quantity': 1}])
        ok, msg, data = self.service.create_order(req)

        self.assertTrue(ok, msg)
        call_args = self.mock_order_repo.create_order_with_items.call_args
        order_data = call_args[0][0]
        self.assertEqual(order_data['cust_id'], 7)


class TestUpdateOrderStatus(unittest.TestCase):

    def setUp(self):
        self.order_repo_patcher = patch('src.services.order_service.OrderRepository')
        self.cust_repo_patcher = patch('src.services.order_service.CustomerRepository')
        self.menu_repo_patcher = patch('src.services.order_service.MenuRepository')

        self.MockOrderRepo = self.order_repo_patcher.start()
        self.cust_repo_patcher.start()
        self.menu_repo_patcher.start()

        self.mock_order_repo = MagicMock()
        self.MockOrderRepo.return_value = self.mock_order_repo

        from src.services.order_service import OrderService
        self.service = OrderService()

    def tearDown(self):
        self.order_repo_patcher.stop()
        self.cust_repo_patcher.stop()
        self.menu_repo_patcher.stop()

    def test_status_update_success(self):
        self.mock_order_repo.update_order_status.return_value = True

        ok, msg = self.service.update_order_status(order_id=1, status_id=2)

        self.assertTrue(ok)

    def test_status_update_failure(self):
        # Repo returns False (e.g. order not found at DB level)
        self.mock_order_repo.update_order_status.return_value = False

        ok, msg = self.service.update_order_status(order_id=999, status_id=2)

        self.assertFalse(ok)
        self.assertIn('failed', msg.lower())


class TestEditOrderItem(unittest.TestCase):

    def setUp(self):
        self.order_repo_patcher = patch('src.services.order_service.OrderRepository')
        self.cust_repo_patcher = patch('src.services.order_service.CustomerRepository')
        self.menu_repo_patcher = patch('src.services.order_service.MenuRepository')

        self.MockOrderRepo = self.order_repo_patcher.start()
        self.cust_repo_patcher.start()
        self.menu_repo_patcher.start()

        self.mock_order_repo = MagicMock()
        self.MockOrderRepo.return_value = self.mock_order_repo

        from src.services.order_service import OrderService
        self.service = OrderService()

    def tearDown(self):
        self.order_repo_patcher.stop()
        self.cust_repo_patcher.stop()
        self.menu_repo_patcher.stop()

    def _setup_order_item(self, status_name='Pending'):
        self.mock_order_repo.find_by_id.side_effect = [
            # find_by_id for kitch_order_item table is called differently
        ]
        self.mock_order_repo.find_by_id.return_value = {
            'order_id': 1,
            'current_status_id': 1,
        }
        self.mock_order_repo.get_all_statuses.return_value = [
            {'status_id': 1, 'status_name': status_name}
        ]

    def test_cannot_edit_completed_order(self):
        # Mock the item lookup
        self.mock_order_repo.find_order_item_by_id.return_value = {
            'order_item_id': 1, 'order_id': 1, 'unit_price': '10.00',
            'is_catering': False, 'catering_size': None,
        }
        self.mock_order_repo.find_by_id.return_value = {
            'order_id': 1, 'current_status_id': 6,
        }
        self.mock_order_repo.get_all_statuses.return_value = [
            {'status_id': 6, 'status_name': 'Completed'}
        ]

        ok, msg, data = self.service.edit_order_item(
            order_item_id=1,
            updates={'quantity': 2},
            changed_by_user_id=1
        )

        self.assertFalse(ok)
        self.assertIn('completed', msg.lower())

    def test_quantity_must_be_positive(self):
        self.mock_order_repo.find_order_item_by_id.return_value = {
            'order_item_id': 1, 'order_id': 1, 'unit_price': '10.00',
            'is_catering': False, 'catering_size': None,
        }
        self.mock_order_repo.find_by_id.return_value = {
            'order_id': 1, 'current_status_id': 1,
        }
        self.mock_order_repo.get_all_statuses.return_value = [
            {'status_id': 1, 'status_name': 'Pending'}
        ]

        ok, msg, data = self.service.edit_order_item(
            order_item_id=1,
            updates={'quantity': 0},
            changed_by_user_id=1
        )

        self.assertFalse(ok)
        self.assertIn('quantity', msg.lower())


class TestRemoveOrderItem(unittest.TestCase):

    def setUp(self):
        self.order_repo_patcher = patch('src.services.order_service.OrderRepository')
        self.cust_repo_patcher = patch('src.services.order_service.CustomerRepository')
        self.menu_repo_patcher = patch('src.services.order_service.MenuRepository')

        self.MockOrderRepo = self.order_repo_patcher.start()
        self.cust_repo_patcher.start()
        self.menu_repo_patcher.start()

        self.mock_order_repo = MagicMock()
        self.MockOrderRepo.return_value = self.mock_order_repo

        from src.services.order_service import OrderService
        self.service = OrderService()

    def tearDown(self):
        self.order_repo_patcher.stop()
        self.cust_repo_patcher.stop()
        self.menu_repo_patcher.stop()

    def test_cannot_remove_last_item(self):
        # Simulate the repo raising ValueError when deleting the last item
        self.mock_order_repo.find_order_item_by_id.return_value = {
            'order_item_id': 1, 'order_id': 1,
        }
        self.mock_order_repo.find_by_id.return_value = {
            'order_id': 1, 'current_status_id': 1,
        }
        self.mock_order_repo.get_all_statuses.return_value = [
            {'status_id': 1, 'status_name': 'Pending'}
        ]
        self.mock_order_repo.delete_order_item.side_effect = ValueError(
            "Cannot remove last item from order"
        )

        ok, msg, data = self.service.remove_order_item(
            order_item_id=1,
            changed_by_user_id=1
        )

        self.assertFalse(ok)
        self.assertIn('last', msg.lower())


class TestUpdateOrderMetadata(unittest.TestCase):

    def setUp(self):
        self.order_repo_patcher = patch('src.services.order_service.OrderRepository')
        self.cust_repo_patcher = patch('src.services.order_service.CustomerRepository')
        self.menu_repo_patcher = patch('src.services.order_service.MenuRepository')

        self.MockOrderRepo = self.order_repo_patcher.start()
        self.cust_repo_patcher.start()
        self.menu_repo_patcher.start()

        self.mock_order_repo = MagicMock()
        self.MockOrderRepo.return_value = self.mock_order_repo

        from src.services.order_service import OrderService
        self.service = OrderService()

    def tearDown(self):
        self.order_repo_patcher.stop()
        self.cust_repo_patcher.stop()
        self.menu_repo_patcher.stop()

    def _setup_active_order(self):
        self.mock_order_repo.find_by_id.return_value = {
            'order_id': 1,
            'current_status_id': 1,
        }
        self.mock_order_repo.get_all_statuses.return_value = [
            {'status_id': 1, 'status_name': 'Pending'}
        ]

    def test_invalid_discount_type_rejected(self):
        self._setup_active_order()

        ok, msg, data = self.service.update_order_metadata(
            order_id=1,
            updates={'discount': {'type': 'invalid', 'value': 10}},
            changed_by_user_id=1
        )

        self.assertFalse(ok)
        self.assertIsNone(data)

    def test_tip_update_success(self):
        self._setup_active_order()
        self.mock_order_repo.update_order_with_audit.return_value = True
        self.mock_order_repo.get_order_with_items.return_value = {
            'order_id': 1, 'items': []
        }

        ok, msg, data = self.service.update_order_metadata(
            order_id=1,
            updates={'tip_amount': 5.00},
            changed_by_user_id=1
        )

        self.assertTrue(ok)
        self.assertIsNotNone(data)


if __name__ == '__main__':
    unittest.main()
