"""Unit tests for validators.py — phone, email, order items, discount, payment validation."""
import unittest

from src.utils.validators import (
    validate_phone,
    validate_email,
    validate_order_items,
    validate_discount,
    validate_payment_method,
    validate_payment_status,
)


class TestValidatePhone(unittest.TestCase):

    def test_valid_10_digit(self):
        ok, result = validate_phone('1234567890')
        self.assertTrue(ok)
        self.assertEqual(result, '1234567890')

    def test_strips_dashes(self):
        ok, result = validate_phone('123-456-7890')
        self.assertTrue(ok)
        self.assertEqual(result, '1234567890')

    def test_strips_spaces(self):
        ok, result = validate_phone('123 456 7890')
        self.assertTrue(ok)
        self.assertEqual(result, '1234567890')

    def test_strips_parentheses_and_spaces(self):
        ok, result = validate_phone('(123) 456-7890')
        self.assertTrue(ok)
        self.assertEqual(result, '1234567890')

    def test_too_short(self):
        ok, msg = validate_phone('123456789')
        self.assertFalse(ok)
        self.assertIn('10 digits', msg)

    def test_too_long(self):
        ok, msg = validate_phone('12345678901')
        self.assertFalse(ok)
        self.assertIn('10 digits', msg)

    def test_empty_string(self):
        ok, msg = validate_phone('')
        self.assertFalse(ok)

    def test_none_value(self):
        ok, msg = validate_phone(None)
        self.assertFalse(ok)

    def test_non_digits_only(self):
        ok, msg = validate_phone('abcdefghij')
        self.assertFalse(ok)


class TestValidateEmail(unittest.TestCase):

    def test_valid_email(self):
        ok, _ = validate_email('user@example.com')
        self.assertTrue(ok)

    def test_valid_email_with_subdomain(self):
        ok, _ = validate_email('user@mail.example.co.uk')
        self.assertTrue(ok)

    def test_missing_at(self):
        ok, msg = validate_email('userexample.com')
        self.assertFalse(ok)

    def test_missing_domain(self):
        ok, msg = validate_email('user@')
        self.assertFalse(ok)

    def test_missing_tld(self):
        ok, msg = validate_email('user@example')
        self.assertFalse(ok)

    def test_empty_string(self):
        ok, msg = validate_email('')
        self.assertFalse(ok)

    def test_none_value(self):
        ok, msg = validate_email(None)
        self.assertFalse(ok)


class TestValidateOrderItems(unittest.TestCase):

    def test_valid_single_item(self):
        items = [{'kic_id': 1, 'quantity': 2}]
        errors = validate_order_items(items)
        self.assertEqual(errors, [])

    def test_valid_multiple_items(self):
        items = [
            {'kic_id': 1, 'quantity': 1},
            {'kic_id': 2, 'quantity': 3},
        ]
        errors = validate_order_items(items)
        self.assertEqual(errors, [])

    def test_empty_list(self):
        errors = validate_order_items([])
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('required' in e.lower() or 'least' in e.lower() for e in errors))

    def test_none_items(self):
        errors = validate_order_items(None)
        self.assertGreater(len(errors), 0)

    def test_missing_kic_id(self):
        items = [{'quantity': 2}]
        errors = validate_order_items(items)
        self.assertTrue(any('kic_id' in e for e in errors))

    def test_zero_quantity(self):
        items = [{'kic_id': 1, 'quantity': 0}]
        errors = validate_order_items(items)
        self.assertGreater(len(errors), 0)

    def test_negative_quantity(self):
        items = [{'kic_id': 1, 'quantity': -1}]
        errors = validate_order_items(items)
        self.assertGreater(len(errors), 0)

    def test_catering_missing_size(self):
        items = [{'kic_id': 1, 'quantity': 1, 'is_catering': True}]
        errors = validate_order_items(items)
        self.assertTrue(any('catering_size' in e for e in errors))

    def test_catering_invalid_size(self):
        items = [{'kic_id': 1, 'quantity': 1, 'is_catering': True, 'catering_size': 'xl'}]
        errors = validate_order_items(items)
        self.assertGreater(len(errors), 0)

    def test_catering_valid_size_small(self):
        items = [{'kic_id': 1, 'quantity': 1, 'is_catering': True, 'catering_size': 'small'}]
        errors = validate_order_items(items)
        self.assertEqual(errors, [])

    def test_catering_valid_size_medium(self):
        items = [{'kic_id': 1, 'quantity': 1, 'is_catering': True, 'catering_size': 'medium'}]
        errors = validate_order_items(items)
        self.assertEqual(errors, [])

    def test_catering_valid_size_large(self):
        items = [{'kic_id': 1, 'quantity': 1, 'is_catering': True, 'catering_size': 'large'}]
        errors = validate_order_items(items)
        self.assertEqual(errors, [])


class TestValidateDiscount(unittest.TestCase):

    def test_valid_percent(self):
        errors = validate_discount('percent', 10)
        self.assertEqual(errors, [])

    def test_valid_fixed(self):
        errors = validate_discount('fixed', 5)
        self.assertEqual(errors, [])

    def test_percent_zero(self):
        errors = validate_discount('percent', 0)
        self.assertEqual(errors, [])

    def test_percent_100(self):
        errors = validate_discount('percent', 100)
        self.assertEqual(errors, [])

    def test_percent_over_100(self):
        errors = validate_discount('percent', 101)
        self.assertGreater(len(errors), 0)

    def test_invalid_type(self):
        errors = validate_discount('amount', 10)
        self.assertTrue(any('percent' in e or 'fixed' in e for e in errors))

    def test_negative_value(self):
        errors = validate_discount('fixed', -5)
        self.assertGreater(len(errors), 0)

    def test_negative_percent_value(self):
        errors = validate_discount('percent', -1)
        self.assertGreater(len(errors), 0)


class TestValidatePaymentMethod(unittest.TestCase):

    def test_cash(self):
        ok, _ = validate_payment_method('cash')
        self.assertTrue(ok)

    def test_card(self):
        ok, _ = validate_payment_method('card')
        self.assertTrue(ok)

    def test_other(self):
        ok, _ = validate_payment_method('other')
        self.assertTrue(ok)

    def test_invalid_method(self):
        ok, msg = validate_payment_method('bitcoin')
        self.assertFalse(ok)
        self.assertIn('cash', msg)

    def test_empty_string(self):
        ok, msg = validate_payment_method('')
        self.assertFalse(ok)

    def test_case_sensitive(self):
        ok, _ = validate_payment_method('Cash')
        self.assertFalse(ok)


class TestValidatePaymentStatus(unittest.TestCase):

    def test_pending(self):
        ok, _ = validate_payment_status('pending')
        self.assertTrue(ok)

    def test_paid(self):
        ok, _ = validate_payment_status('paid')
        self.assertTrue(ok)

    def test_partially_paid(self):
        ok, _ = validate_payment_status('partially_paid')
        self.assertTrue(ok)

    def test_refunded(self):
        ok, _ = validate_payment_status('refunded')
        self.assertTrue(ok)

    def test_cancelled(self):
        ok, _ = validate_payment_status('cancelled')
        self.assertTrue(ok)

    def test_invalid_status(self):
        ok, msg = validate_payment_status('unknown')
        self.assertFalse(ok)

    def test_empty_string(self):
        ok, msg = validate_payment_status('')
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main()
