from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserRegistrationTests(APITestCase):
    def test_register_creates_user(self):
        url = reverse("users:register")
        payload = {
            "username": "johndoe",
            "email": "john@example.com",
            "password": "StrongPass123!",
            "phone_number": "+998901234567",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="johndoe").exists())
        user = User.objects.get(username="johndoe")
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_register_duplicate_username_fails(self):
        User.objects.create_user(username="johndoe", password="pass12345")
        url = reverse("users:register")
        response = self.client.post(url, {"username": "johndoe", "password": "StrongPass123!"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="jane", password="StrongPass123!")

    def test_me_requires_auth(self):
        response = self.client.get(reverse("users:me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_profile_when_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("users:me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "jane")

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("users:change-password"),
            {"old_password": "StrongPass123!", "new_password": "NewStrongPass456!"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass456!"))
