from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Brand

User = get_user_model()


class BrandTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")
        self.brand = Brand.objects.create(name="Applied Nutrition", is_active=True)

    def test_list_brands_is_public(self):
        response = self.client.get(reverse("brands:brand-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_requires_admin(self):
        response = self.client.post(reverse("brands:brand-list"), {"name": "Optimum Nutrition"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_create_brand(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("brands:brand-list"), {"name": "Optimum Nutrition"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["slug"], "optimum-nutrition")
