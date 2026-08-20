from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class SiteSettingsTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")

    def test_get_is_public_and_autocreates(self):
        response = self.client.get(reverse("site_settings:site-settings"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["site_name"], "NutriZone")

    def test_patch_requires_admin(self):
        response = self.client.patch(reverse("site_settings:site-settings"), {"site_name": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_update_settings(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(reverse("site_settings:site-settings"), {"currency": "USD"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["currency"], "USD")
