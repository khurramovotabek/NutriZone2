from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.brand.models import Brand
from apps.shared.test_helpers import make_category, make_product

from .models import ProductSpecification, ProductVariant

User = get_user_model()


class ProductCatalogTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")
        self.category = make_category("Protein")
        self.brand = Brand.objects.create(name="Applied Nutrition")
        self.product = make_product(
            "Whey Protein",
            category=self.category,
            brand=self.brand,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, sku="WP-1KG", price=Decimal("29.99"), quantity=10, is_default=True
        )
        ProductSpecification.objects.create(product=self.product, label="Protein", value="24g", sort_order=1)

    def test_list_products_public(self):
        response = self.client.get(reverse("products:product-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_detail_returns_nested_data_in_one_request(self):
        response = self.client.get(reverse("products:product-detail", kwargs={"slug": self.product.slug}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["variants"]), 1)
        self.assertEqual(len(response.data["specifications"]), 1)
        self.assertIn("related_products", response.data)

    def test_detail_returns_translated_name(self):
        response = self.client.get(reverse("products:product-detail", kwargs={"slug": self.product.slug}))
        self.assertEqual(response.data["name"], "Whey Protein")
        self.assertEqual(response.data["language"], "en")

    def test_search_by_sku(self):
        response = self.client.get(reverse("products:product-list"), {"search": "WP-1KG"})
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_category_slug(self):
        response = self.client.get(reverse("products:product-list"), {"category": self.category.slug})
        self.assertEqual(response.data["count"], 1)

    def test_out_of_stock_variant_blocks_purchase_intent(self):
        self.variant.quantity = 0
        self.variant.save()
        response = self.client.get(reverse("products:product-detail", kwargs={"slug": self.product.slug}))
        self.assertFalse(any(v["is_in_stock"] for v in response.data["variants"]))

    def test_duplicate_sku_rejected(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("products:product-variant-list", kwargs={"product_slug": self.product.slug})
        response = self.client.post(url, {"sku": "WP-1KG", "price": "19.99", "quantity": 5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_requires_admin(self):
        response = self.client.post(
            reverse("products:product-list"),
            {"category": str(self.category.id), "brand": str(self.brand.id), "slug": "new-product"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProductTranslationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")
        self.category = make_category("Protein")
        self.brand = Brand.objects.create(name="Applied Nutrition")
        self.product = make_product("Whey Protein", category=self.category, brand=self.brand)

    def _translations_url(self):
        return reverse("products:product-translation-list", kwargs={"product_slug": self.product.slug})

    def test_add_translation_requires_admin(self):
        response = self.client.post(
            self._translations_url(), {"language": "ru", "name": "Сывороточный протеин"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_add_translation_and_it_is_served(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            self._translations_url(), {"language": "ru", "name": "Сывороточный протеин"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        detail = self.client.get(
            reverse("products:product-detail", kwargs={"slug": self.product.slug}), {"lang": "ru"}
        )
        self.assertEqual(detail.data["name"], "Сывороточный протеин")
        self.assertEqual(detail.data["language"], "ru")
        self.assertTrue(detail.data["translation_available"])

    def test_missing_language_falls_back_to_english_and_flags_it(self):
        response = self.client.get(
            reverse("products:product-detail", kwargs={"slug": self.product.slug}), {"lang": "ru"}
        )
        self.assertEqual(response.data["name"], "Whey Protein")
        self.assertEqual(response.data["language"], "en")
        self.assertFalse(response.data["translation_available"])
        self.assertEqual(response.data["requested_language"], "ru")

    def test_duplicate_language_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self._translations_url(), {"language": "en", "name": "Duplicate"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProductQueryCountTests(APITestCase):
    """Verifies the translation prefetching actually prevents N+1 queries --
    the specific concern called out for this feature: listing 100 products
    should NOT execute ~100 translation queries."""

    def setUp(self):
        category = make_category("Protein")
        brand = Brand.objects.create(name="Applied Nutrition")
        for i in range(15):
            product = make_product(f"Product {i}", category=category, brand=brand, slug=f"product-{i}")
            ProductVariant.objects.create(
                product=product, sku=f"SKU-{i}", price=Decimal("10.00"), quantity=5, is_default=True
            )

    def test_listing_many_products_has_constant_query_count(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        url = reverse("products:product-list")

        with CaptureQueriesContext(connection) as small:
            self.client.get(url, {"page_size": 5})
        small_count = len(small.captured_queries)

        # Add more products and confirm the query count doesn't grow with N.
        category = make_category("More", slug="more-category")
        brand = Brand.objects.create(name="Another Brand")
        for i in range(15, 30):
            product = make_product(f"Product {i}", category=category, brand=brand, slug=f"product-{i}")
            ProductVariant.objects.create(
                product=product, sku=f"SKU-{i}", price=Decimal("10.00"), quantity=5, is_default=True
            )

        with CaptureQueriesContext(connection) as large:
            self.client.get(url, {"page_size": 30})
        large_count = len(large.captured_queries)

        # A handful more queries is fine (pagination count, etc.) but it
        # must not scale linearly with the number of products serialized.
        self.assertLess(large_count, small_count + 5)
