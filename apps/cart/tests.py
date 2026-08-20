from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.brand.models import Brand
from apps.products.models import ProductVariant
from apps.shared.test_helpers import make_category, make_product


class CartTests(APITestCase):
    def setUp(self):
        category = make_category("Protein")
        brand = Brand.objects.create(name="Applied Nutrition")
        self.product = make_product("Whey Protein", category=category, brand=brand)
        self.variant = ProductVariant.objects.create(
            product=self.product, sku="WP-1KG", price=Decimal("29.99"), quantity=5
        )

    def test_add_item_creates_cart(self):
        response = self.client.post(
            reverse("cart:cart-item-list"), {"variant": str(self.variant.id), "quantity": 2}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_quantity"], 2)
        self.assertEqual(Decimal(response.data["subtotal"]), Decimal("59.98"))

    def test_cannot_add_more_than_stock(self):
        response = self.client.post(
            reverse("cart:cart-item-list"), {"variant": str(self.variant.id), "quantity": 10}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cart_persists_via_cart_id_header(self):
        first = self.client.post(
            reverse("cart:cart-item-list"), {"variant": str(self.variant.id), "quantity": 1}
        )
        cart_id = first["X-Cart-Id"]
        second = self.client.get(reverse("cart:cart-detail"), HTTP_X_CART_ID=cart_id)
        self.assertEqual(second.data["total_quantity"], 1)

    def test_decrease_to_zero_removes_item(self):
        add = self.client.post(
            reverse("cart:cart-item-list"), {"variant": str(self.variant.id), "quantity": 1}
        )
        cart_id = add["X-Cart-Id"]
        item_id = add.data["items"][0]["id"]
        response = self.client.post(
            reverse("cart:cart-item-decrease", kwargs={"item_id": item_id}), HTTP_X_CART_ID=cart_id
        )
        self.assertEqual(response.data["total_items"], 0)
