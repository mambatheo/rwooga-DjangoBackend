from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from products.models import (
    ServiceCategory,
    Product,
    Discount,
    ProductDiscount
)


class DiscountModelTest(TestCase):

    def test_discount_is_valid_when_active_and_in_date_range(self):
        discount = Discount.objects.create(
            name="Valid Discount",
            discount_type=Discount.PERCENTAGE,
            discount_value=Decimal("10"),
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            is_active=True
        )

        self.assertTrue(discount.is_valid())

    def test_discount_is_invalid_when_expired(self):
        discount = Discount.objects.create(
            name="Expired Discount",
            discount_type=Discount.FIXED,
            discount_value=Decimal("500"),
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() - timedelta(days=5),
            is_active=True
        )

        self.assertFalse(discount.is_valid())


class ProductPricingTest(TestCase):

    def setUp(self):
        self.category = ServiceCategory.objects.create(
            name="Furniture"
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Chair",
            short_description="Wooden chair",
            detailed_description="Strong wooden chair",
            unit_price=Decimal("10000"),
            length=Decimal("10"),
            width=Decimal("10"),
            height=Decimal("10"),
            published=True
        )

        self.discount = Discount.objects.create(
            name="10 Percent OFF",
            discount_type=Discount.PERCENTAGE,
            discount_value=Decimal("10"),
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            is_active=True
        )

        ProductDiscount.objects.create(
            product=self.product,
            discount=self.discount,
            is_valid=True
        )

    def test_final_price_with_percentage_discount(self):
        final_price = self.product.get_final_price()
        self.assertEqual(final_price, Decimal("9000.00"))

    def test_final_price_with_fixed_discount(self):
        self.discount.discount_type = Discount.FIXED
        self.discount.discount_value = Decimal("2000")
        self.discount.save()

        final_price = self.product.get_final_price()
        self.assertEqual(final_price, Decimal("8000.00"))

    def test_price_never_goes_below_zero(self):
        self.discount.discount_type = Discount.FIXED
        self.discount.discount_value = Decimal("20000")
        self.discount.save()

        final_price = self.product.get_final_price()
        self.assertEqual(final_price, Decimal("0.00"))
