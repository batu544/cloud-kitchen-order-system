"""Unit tests for payment_service.py with mocked repositories."""
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestRecordPayment(unittest.TestCase):

    def setUp(self):
        self.payment_repo_patcher = patch('src.services.payment_service.PaymentRepository')
        self.order_repo_patcher = patch('src.services.payment_service.OrderRepository')

        self.MockPaymentRepo = self.payment_repo_patcher.start()
        self.MockOrderRepo = self.order_repo_patcher.start()

        self.mock_payment_repo = MagicMock()
        self.mock_order_repo = MagicMock()
        self.MockPaymentRepo.return_value = self.mock_payment_repo
        self.MockOrderRepo.return_value = self.mock_order_repo

        from src.services.payment_service import PaymentService
        self.service = PaymentService()

    def tearDown(self):
        self.payment_repo_patcher.stop()
        self.order_repo_patcher.stop()

    def _setup_order(self, total_amount=100.00):
        self.mock_order_repo.get_order_with_items.return_value = {
            'order_id': 1,
            'total_amount': total_amount,
            'current_status_id': 1,
        }

    def test_record_full_payment_marks_paid(self):
        self._setup_order(total_amount=100.00)
        self.mock_payment_repo.create_payment.return_value = 10
        self.mock_payment_repo.get_total_paid_for_order.return_value = Decimal('100.00')

        ok, msg, data = self.service.record_payment(
            order_id=1,
            amount=100.00,
            payment_method='cash',
            payment_status='paid'
        )

        self.assertTrue(ok)
        self.assertEqual(data['order_payment_status'], 'paid')
        self.mock_order_repo.update_payment_status.assert_called_with(1, 'paid')

    def test_record_partial_payment_marks_partially_paid(self):
        self._setup_order(total_amount=100.00)
        self.mock_payment_repo.create_payment.return_value = 11
        self.mock_payment_repo.get_total_paid_for_order.return_value = Decimal('50.00')

        ok, msg, data = self.service.record_payment(
            order_id=1,
            amount=50.00,
            payment_method='card',
            payment_status='paid'
        )

        self.assertTrue(ok)
        self.assertEqual(data['order_payment_status'], 'partially_paid')

    def test_invalid_payment_method(self):
        ok, msg, data = self.service.record_payment(
            order_id=1,
            amount=100.00,
            payment_method='bitcoin',
            payment_status='paid'
        )

        self.assertFalse(ok)
        self.assertIsNone(data)

    def test_invalid_payment_status(self):
        ok, msg, data = self.service.record_payment(
            order_id=1,
            amount=100.00,
            payment_method='cash',
            payment_status='unknown'
        )

        self.assertFalse(ok)
        self.assertIsNone(data)

    def test_order_not_found(self):
        self.mock_order_repo.get_order_with_items.return_value = None

        ok, msg, data = self.service.record_payment(
            order_id=999,
            amount=100.00,
            payment_method='cash',
            payment_status='paid'
        )

        self.assertFalse(ok)
        self.assertIn('not found', msg.lower())
        self.assertIsNone(data)

    def test_tip_amount_stored(self):
        self._setup_order(total_amount=100.00)
        self.mock_payment_repo.create_payment.return_value = 12
        self.mock_payment_repo.get_total_paid_for_order.return_value = Decimal('110.00')

        ok, msg, data = self.service.record_payment(
            order_id=1,
            amount=100.00,
            payment_method='cash',
            payment_status='paid',
            tip_amount=10.00
        )

        self.assertTrue(ok)
        self.assertEqual(data['tip_amount'], 10.00)
        # Verify create_payment was called with tip_amount
        call_kwargs = self.mock_payment_repo.create_payment.call_args[1]
        self.assertEqual(call_kwargs['tip_amount'], Decimal('10.00'))

    def test_override_requires_reason(self):
        self._setup_order()

        ok, msg, data = self.service.record_payment(
            order_id=1,
            amount=100.00,
            payment_method='cash',
            payment_status='paid',
            override_amount=80.00,
            override_reason=None  # missing reason
        )

        self.assertFalse(ok)
        self.assertIn('reason', msg.lower())

    def test_override_negative_amount(self):
        self._setup_order()

        ok, msg, data = self.service.record_payment(
            order_id=1,
            amount=100.00,
            payment_method='cash',
            payment_status='paid',
            override_amount=-10.00,
            override_reason='discount'
        )

        self.assertFalse(ok)

    def test_override_uses_override_amount_for_comparison(self):
        self._setup_order(total_amount=100.00)
        self.mock_payment_repo.create_payment.return_value = 13
        self.mock_payment_repo.get_total_paid_for_order.return_value = Decimal('80.00')

        ok, msg, data = self.service.record_payment(
            order_id=1,
            amount=80.00,
            payment_method='cash',
            payment_status='paid',
            override_amount=80.00,
            override_reason='Staff discount applied'
        )

        self.assertTrue(ok)
        self.assertEqual(data['order_payment_status'], 'paid')


class TestGetOrderPayments(unittest.TestCase):

    def setUp(self):
        self.payment_repo_patcher = patch('src.services.payment_service.PaymentRepository')
        self.order_repo_patcher = patch('src.services.payment_service.OrderRepository')

        self.MockPaymentRepo = self.payment_repo_patcher.start()
        self.MockOrderRepo = self.order_repo_patcher.start()

        self.mock_payment_repo = MagicMock()
        self.mock_order_repo = MagicMock()
        self.MockPaymentRepo.return_value = self.mock_payment_repo
        self.MockOrderRepo.return_value = self.mock_order_repo

        from src.services.payment_service import PaymentService
        self.service = PaymentService()

    def tearDown(self):
        self.payment_repo_patcher.stop()
        self.order_repo_patcher.stop()

    def test_get_payments_success(self):
        self.mock_payment_repo.get_payments_for_order.return_value = [
            {'payment_id': 1, 'amount': 50.00},
            {'payment_id': 2, 'amount': 50.00},
        ]
        self.mock_payment_repo.get_total_paid_for_order.return_value = Decimal('100.00')

        ok, msg, data = self.service.get_order_payments(1)

        self.assertTrue(ok)
        self.assertEqual(len(data['payments']), 2)
        self.assertEqual(data['total_paid'], 100.00)

    def test_get_payments_empty_order(self):
        self.mock_payment_repo.get_payments_for_order.return_value = []
        self.mock_payment_repo.get_total_paid_for_order.return_value = Decimal('0.00')

        ok, msg, data = self.service.get_order_payments(1)

        self.assertTrue(ok)
        self.assertEqual(data['payments'], [])
        self.assertEqual(data['total_paid'], 0.00)


if __name__ == '__main__':
    unittest.main()
