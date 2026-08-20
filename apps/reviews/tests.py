from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.brand.models import Brand
from apps.notifications.models import Notification
from apps.orders.models import Order, OrderItem
from apps.products.models import ProductVariant
from apps.shared.test_helpers import make_category, make_product

from .models import Review, ReviewReply, ReviewReport

User = get_user_model()


class ReviewTests(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username="buyer", password="StrongPass123!")
        self.other_user = User.objects.create_user(username="other", password="StrongPass123!")
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")

        category = make_category("Protein")
        brand = Brand.objects.create(name="Optimum Nutrition")
        self.product = make_product("Gold Standard Whey", category=category, brand=brand)
        self.variant = ProductVariant.objects.create(
            product=self.product, sku="ON-GSW-900", price=Decimal("49.99"), quantity=10
        )

        self.delivered_order = Order.objects.create(
            user=self.buyer,
            full_name="Buyer",
            phone_number="+998901234567",
            delivery_address="Somewhere",
            status=Order.Status.ACCEPTED,
        )
        OrderItem.objects.create(
            order=self.delivered_order,
            variant=self.variant,
            product_name="Gold Standard Whey",
            variant_name="900g",
            sku=self.variant.sku,
            price=self.variant.price,
            quantity=1,
        )

    def _review_list_url(self):
        return reverse("product-review-list", kwargs={"product_slug": self.product.slug})

    def test_verified_buyer_can_review(self):
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(self._review_list_url(), {"rating": 5, "comment": "Excellent!"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_verified_purchase"])

    def test_non_buyer_cannot_review(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(self._review_list_url(), {"rating": 4, "comment": "Looks good"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "purchase_not_verified")

    def test_anonymous_cannot_review(self):
        response = self.client.post(self._review_list_url(), {"rating": 4})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_review_rejected(self):
        self.client.force_authenticate(user=self.buyer)
        self.client.post(self._review_list_url(), {"rating": 5, "comment": "Great"})
        response = self.client.post(self._review_list_url(), {"rating": 3, "comment": "Again"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "duplicate_review")

    def test_rating_out_of_range_rejected(self):
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(self._review_list_url(), {"rating": 7})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_list_is_public(self):
        Review.objects.create(product=self.product, user=self.buyer, rating=5, is_verified_purchase=True)
        response = self.client.get(self._review_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_rating_summary(self):
        Review.objects.create(product=self.product, user=self.buyer, rating=5, is_verified_purchase=True)
        Review.objects.create(
            product=self.product, user=self.other_user, rating=3, is_verified_purchase=False
        )
        url = reverse("product-review-summary", kwargs={"product_slug": self.product.slug})
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(response.data["average"], 4.0)

    def test_owner_can_update_review(self):
        review = Review.objects.create(
            product=self.product, user=self.buyer, rating=2, comment="meh", is_verified_purchase=True
        )
        self.client.force_authenticate(user=self.buyer)
        response = self.client.patch(
            reverse("reviews:review-detail", kwargs={"pk": review.id}), {"rating": 5}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)

    def test_other_user_cannot_update_review(self):
        review = Review.objects.create(
            product=self.product, user=self.buyer, rating=2, is_verified_purchase=True
        )
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(
            reverse("reviews:review-detail", kwargs={"pk": review.id}), {"rating": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_any_review(self):
        review = Review.objects.create(
            product=self.product, user=self.buyer, rating=2, is_verified_purchase=True
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(reverse("reviews:review-detail", kwargs={"pk": review.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ReviewReplyTests(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username="buyer", password="StrongPass123!")
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")
        category = make_category("Protein")
        brand = Brand.objects.create(name="Optimum Nutrition")
        self.product = make_product("Gold Standard Whey", category=category, brand=brand)
        self.review = Review.objects.create(
            product=self.product, user=self.buyer, rating=5, comment="Great!", is_verified_purchase=True
        )

    def test_non_admin_cannot_reply(self):
        response = self.client.post(
            reverse("reviews:review-reply-create", kwargs={"pk": self.review.id}), {"message": "Thanks!"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_reply_via_api_creates_notification(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("reviews:review-reply-create", kwargs={"pk": self.review.id}),
            {"message": "Thanks for the kind words!"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_admin_reply"])

        notification = Notification.objects.get(recipient=self.buyer)
        self.assertEqual(notification.notification_type, "review_reply")
        self.assertIn("Gold Standard Whey", notification.body)
        self.assertIn("reviews", notification.link_path)

    def test_admin_reply_via_admin_inline_also_creates_notification(self):
        # Simulates the Django admin inline save path, which bypasses
        # ReviewReplyService entirely -- the signal must still fire.
        ReviewReply.objects.create(review=self.review, admin_user=self.admin, message="Via admin inline")
        self.assertTrue(
            Notification.objects.filter(recipient=self.buyer, notification_type="review_reply").exists()
        )

    def test_reply_appears_in_review_list(self):
        ReviewReply.objects.create(review=self.review, admin_user=self.admin, message="Thanks!")
        response = self.client.get(reverse("product-review-list", kwargs={"product_slug": self.product.slug}))
        self.assertEqual(len(response.data["results"][0]["replies"]), 1)
        self.assertEqual(response.data["results"][0]["replies"][0]["message"], "Thanks!")


class ReviewHelpfulAndReportTests(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username="buyer", password="StrongPass123!")
        self.voter = User.objects.create_user(username="voter", password="StrongPass123!")
        category = make_category("Protein")
        brand = Brand.objects.create(name="Optimum Nutrition")
        product = make_product("Gold Standard Whey", category=category, brand=brand)
        self.review = Review.objects.create(
            product=product, user=self.buyer, rating=5, is_verified_purchase=True
        )

    def test_toggle_helpful_requires_auth(self):
        response = self.client.post(reverse("reviews:review-helpful-toggle", kwargs={"pk": self.review.id}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_toggle_helpful_marks_then_unmarks(self):
        self.client.force_authenticate(user=self.voter)
        url = reverse("reviews:review-helpful-toggle", kwargs={"pk": self.review.id})

        first = self.client.post(url)
        self.assertTrue(first.data["is_marked_helpful_by_me"])
        self.assertEqual(first.data["helpful_count"], 1)

        second = self.client.post(url)
        self.assertFalse(second.data["is_marked_helpful_by_me"])
        self.assertEqual(second.data["helpful_count"], 0)

    def test_report_review(self):
        self.client.force_authenticate(user=self.voter)
        response = self.client.post(
            reverse("reviews:review-report", kwargs={"pk": self.review.id}),
            {"reason": "spam", "comment": "Looks like an ad"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReviewReport.objects.filter(review=self.review).count(), 1)

    def test_duplicate_report_rejected(self):
        self.client.force_authenticate(user=self.voter)
        url = reverse("reviews:review-report", kwargs={"pk": self.review.id})
        self.client.post(url, {"reason": "spam"})
        response = self.client.post(url, {"reason": "fake"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
