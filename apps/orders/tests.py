from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.brand.models import Brand
from apps.locations.models import City, Country, Region
from apps.products.models import ProductVariant
from apps.shared.test_helpers import make_category, make_product

User = get_user_model()


class OrderWorkflowTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")
        category = make_category("Protein")
        brand = Brand.objects.create(name="Applied Nutrition")
        self.product = make_product("Whey Protein", category=category, brand=brand)
        self.variant = ProductVariant.objects.create(
            product=self.product, sku="WP-1KG", price=Decimal("29.99"), quantity=5
        )
        self.country = Country.objects.create(name="Uzbekistan", code="UZ")
        self.region = Region.objects.create(country=self.country, name="Tashkent Region")
        self.city = City.objects.create(region=self.region, name="Tashkent")

    def _checkout_payload(self, **overrides):
        payload = {
            "full_name": "John Doe",
            "phone_number": "+998901234567",
            "telegram_username": "johndoe",
            "country": str(self.country.id),
            "region": str(self.region.id),
            "city": str(self.city.id),
            "delivery_address": "123 Main St",
            "comment": "Leave at the door",
        }
        payload.update(overrides)
        return payload

    def _add_to_cart(self, quantity=2):
        response = self.client.post(
            reverse("cart:cart-item-list"), {"variant": str(self.variant.id), "quantity": quantity}
        )
        return response["X-Cart-Id"]

    def test_checkout_creates_order_and_does_not_touch_stock(self):
        cart_id = self._add_to_cart(2)
        response = self.client.post(
            reverse("orders:order-list"),
            self._checkout_payload(),
            HTTP_X_CART_ID=cart_id,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "new")
        self.assertEqual(response.data["city_detail"]["name"], "Tashkent")
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.quantity, 5)  # unchanged until PENDING

    def test_checkout_empty_cart_fails(self):
        response = self.client.post(reverse("orders:order-list"), self._checkout_payload())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_rejects_mismatched_region_and_country(self):
        other_country = Country.objects.create(name="Kazakhstan", code="KZ")
        cart_id = self._add_to_cart(1)
        response = self.client.post(
            reverse("orders:order-list"),
            self._checkout_payload(country=str(other_country.id)),
            HTTP_X_CART_ID=cart_id,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_moving_to_pending_decreases_stock(self):
        cart_id = self._add_to_cart(2)
        order_resp = self.client.post(
            reverse("orders:order-list"), self._checkout_payload(), HTTP_X_CART_ID=cart_id
        )
        order_id = order_resp.data["id"]

        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            reverse("orders:order-set-status", kwargs={"pk": order_id}), {"status": "pending"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.quantity, 3)

    def test_cancelling_pending_order_restocks(self):
        cart_id = self._add_to_cart(2)
        order_resp = self.client.post(
            reverse("orders:order-list"), self._checkout_payload(), HTTP_X_CART_ID=cart_id
        )
        order_id = order_resp.data["id"]

        self.client.force_authenticate(user=self.admin)
        self.client.patch(reverse("orders:order-set-status", kwargs={"pk": order_id}), {"status": "pending"})
        self.client.patch(
            reverse("orders:order-set-status", kwargs={"pk": order_id}), {"status": "cancelled"}
        )
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.quantity, 5)

    def test_invalid_transition_rejected(self):
        cart_id = self._add_to_cart(1)
        order_resp = self.client.post(
            reverse("orders:order-list"), self._checkout_payload(), HTTP_X_CART_ID=cart_id
        )
        order_id = order_resp.data["id"]
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            reverse("orders:order-set-status", kwargs={"pk": order_id}), {"status": "accepted"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_snapshots_product_name_in_checkout_language(self):
        from apps.products.models import ProductTranslation

        ProductTranslation.objects.create(product=self.product, language="ru", name="Сывороточный протеин")
        cart_id = self._add_to_cart(1)
        response = self.client.post(
            reverse("orders:order-list") + "?lang=ru",
            self._checkout_payload(),
            HTTP_X_CART_ID=cart_id,
        )
        self.assertEqual(response.data["items"][0]["product_name"], "Сывороточный протеин")

    def test_non_admin_cannot_change_status(self):
        cart_id = self._add_to_cart(1)
        order_resp = self.client.post(
            reverse("orders:order-list"), self._checkout_payload(), HTTP_X_CART_ID=cart_id
        )
        order_id = order_resp.data["id"]
        response = self.client.patch(
            reverse("orders:order-set-status", kwargs={"pk": order_id}), {"status": "pending"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
