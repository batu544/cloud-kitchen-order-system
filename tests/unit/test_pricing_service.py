"""Unit tests for pricing_service.py — catering calculations, discounts, and totals."""
import unittest
from decimal import Decimal

from src.services.pricing_service import (
    calculate_catering_price,
    apply_discount,
    calculate_order_total,
    calculate_line_total,
)


class TestCalculateCateringPrice(unittest.TestCase):

    def test_small_tray(self):
        price = Decimal('10.00')
        result = calculate_catering_price(price, 'small')
        self.assertEqual(result, Decimal('36.00'))  # 10 * 4 * 0.9

    def test_medium_tray(self):
        price = Decimal('10.00')
        result = calculate_catering_price(price, 'medium')
        self.assertEqual(result, Decimal('54.00'))  # 10 * 6 * 0.9

    def test_large_tray(self):
        price = Decimal('10.00')
        result = calculate_catering_price(price, 'large')
        self.assertEqual(result, Decimal('108.00'))  # 10 * 12 * 0.9

    def test_invalid_size_raises(self):
        with self.assertRaises(ValueError):
            calculate_catering_price(Decimal('10.00'), 'xl')

    def test_empty_size_raises(self):
        with self.assertRaises(ValueError):
            calculate_catering_price(Decimal('10.00'), '')

    def test_decimal_precision(self):
        price = Decimal('7.33')
        result = calculate_catering_price(price, 'small')
        # 7.33 * 4 * 0.9 = 26.388 → rounded to 26.39
        self.assertEqual(result, Decimal('26.39'))
        # Result must have exactly 2 decimal places
        self.assertEqual(result, result.quantize(Decimal('0.01')))

    def test_zero_base_price(self):
        result = calculate_catering_price(Decimal('0.00'), 'large')
        self.assertEqual(result, Decimal('0.00'))


class TestApplyDiscount(unittest.TestCase):

    def test_percent_discount_10(self):
        subtotal = Decimal('100.00')
        result = apply_discount(subtotal, 'percent', Decimal('10'))
        self.assertEqual(result, Decimal('10.00'))

    def test_percent_discount_zero(self):
        subtotal = Decimal('100.00')
        result = apply_discount(subtotal, 'percent', Decimal('0'))
        self.assertEqual(result, Decimal('0.00'))

    def test_percent_discount_100(self):
        subtotal = Decimal('100.00')
        result = apply_discount(subtotal, 'percent', Decimal('100'))
        self.assertEqual(result, Decimal('100.00'))

    def test_percent_over_100_raises(self):
        with self.assertRaises(ValueError):
            apply_discount(Decimal('100.00'), 'percent', Decimal('101'))

    def test_percent_negative_raises(self):
        with self.assertRaises(ValueError):
            apply_discount(Decimal('100.00'), 'percent', Decimal('-5'))

    def test_fixed_discount(self):
        subtotal = Decimal('100.00')
        result = apply_discount(subtotal, 'fixed', Decimal('15'))
        self.assertEqual(result, Decimal('15.00'))

    def test_fixed_exceeds_subtotal_is_capped(self):
        subtotal = Decimal('100.00')
        result = apply_discount(subtotal, 'fixed', Decimal('200'))
        self.assertEqual(result, Decimal('100.00'))  # capped at subtotal

    def test_fixed_negative_raises(self):
        with self.assertRaises(ValueError):
            apply_discount(Decimal('100.00'), 'fixed', Decimal('-10'))

    def test_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            apply_discount(Decimal('100.00'), 'amount', Decimal('10'))

    def test_decimal_precision(self):
        subtotal = Decimal('99.99')
        result = apply_discount(subtotal, 'percent', Decimal('10'))
        self.assertEqual(result, result.quantize(Decimal('0.01')))


class TestCalculateOrderTotal(unittest.TestCase):

    def test_basic_with_discount_and_tip(self):
        tax, total = calculate_order_total(
            subtotal=Decimal('100.00'),
            discount_amount=Decimal('10.00'),
            tip_amount=Decimal('5.00')
        )
        self.assertEqual(tax, Decimal('0.00'))
        self.assertEqual(total, Decimal('95.00'))  # 100 - 10 + 5

    def test_no_discount_no_tip(self):
        tax, total = calculate_order_total(
            subtotal=Decimal('75.50'),
            discount_amount=Decimal('0.00'),
            tip_amount=Decimal('0.00')
        )
        self.assertEqual(total, Decimal('75.50'))

    def test_zero_values(self):
        tax, total = calculate_order_total(
            subtotal=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            tip_amount=Decimal('0.00')
        )
        self.assertEqual(total, Decimal('0.00'))

    def test_tax_is_always_zero(self):
        tax, _ = calculate_order_total(
            subtotal=Decimal('200.00'),
            discount_amount=Decimal('20.00'),
            tip_amount=Decimal('10.00')
        )
        self.assertEqual(tax, Decimal('0.00'))

    def test_discount_larger_than_subtotal_results_in_zero(self):
        tax, total = calculate_order_total(
            subtotal=Decimal('50.00'),
            discount_amount=Decimal('100.00'),
            tip_amount=Decimal('0.00')
        )
        self.assertEqual(total, Decimal('0.00'))

    def test_tip_only(self):
        tax, total = calculate_order_total(
            subtotal=Decimal('50.00'),
            discount_amount=Decimal('0.00'),
            tip_amount=Decimal('10.00')
        )
        self.assertEqual(total, Decimal('60.00'))


class TestCalculateLineTotal(unittest.TestCase):

    def test_regular_item(self):
        result = calculate_line_total(
            unit_price=Decimal('10.00'),
            quantity=3
        )
        self.assertEqual(result, Decimal('30.00'))

    def test_regular_item_quantity_one(self):
        result = calculate_line_total(
            unit_price=Decimal('12.50'),
            quantity=1
        )
        self.assertEqual(result, Decimal('12.50'))

    def test_catering_small(self):
        result = calculate_line_total(
            unit_price=Decimal('10.00'),
            quantity=1,
            is_catering=True,
            catering_size='small'
        )
        self.assertEqual(result, Decimal('36.00'))  # 10 * 4 * 0.9

    def test_catering_medium_quantity_two(self):
        result = calculate_line_total(
            unit_price=Decimal('10.00'),
            quantity=2,
            is_catering=True,
            catering_size='medium'
        )
        self.assertEqual(result, Decimal('108.00'))  # (10 * 6 * 0.9) * 2

    def test_catering_large(self):
        result = calculate_line_total(
            unit_price=Decimal('10.00'),
            quantity=1,
            is_catering=True,
            catering_size='large'
        )
        self.assertEqual(result, Decimal('108.00'))  # 10 * 12 * 0.9

    def test_non_catering_ignores_catering_size(self):
        result = calculate_line_total(
            unit_price=Decimal('10.00'),
            quantity=2,
            is_catering=False,
            catering_size='small'
        )
        self.assertEqual(result, Decimal('20.00'))  # regular: 10 * 2

    def test_decimal_precision(self):
        result = calculate_line_total(unit_price=Decimal('7.33'), quantity=3)
        self.assertEqual(result, result.quantize(Decimal('0.01')))


if __name__ == '__main__':
    unittest.main()
