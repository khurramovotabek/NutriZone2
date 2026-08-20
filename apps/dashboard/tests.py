from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.brand.models import Brand
from apps.products.models import ProductVariant
from apps.shared.test_helpers import make_category, make_product

User = get_user_model()


class DashboardTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")
        category = make_category("Protein")
        brand = Brand.objects.create(name="Applied Nutrition")
        product = make_product("Whey Protein", category=category, brand=brand)
        ProductVariant.objects.create(product=product, sku="WP-1KG", price=Decimal("29.99"), quantity=2)

    def test_overview_requires_admin(self):
        response = self.client.get(reverse("dashboard:overview"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_sees_overview(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("dashboard:overview"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_products"], 1)
        self.assertEqual(len(response.data["low_stock_variants"]), 1)
