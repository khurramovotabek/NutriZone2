from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class MediaFileTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")

    def test_upload_requires_admin(self):
        image = SimpleUploadedFile("test.jpg", b"fake-image-bytes", content_type="image/jpeg")
        response = self.client.post(reverse("media:media-list"), {"file": image, "folder": "banners"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_upload_allowed_type(self):
        self.client.force_authenticate(user=self.admin)
        image = SimpleUploadedFile("test.jpg", b"fake-image-bytes", content_type="image/jpeg")
        response = self.client.post(reverse("media:media-list"), {"file": image, "folder": "banners"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_disallowed_extension_rejected(self):
        self.client.force_authenticate(user=self.admin)
        bad_file = SimpleUploadedFile("virus.exe", b"bad-bytes", content_type="application/octet-stream")
        response = self.client.post(reverse("media:media-list"), {"file": bad_file, "folder": "banners"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
