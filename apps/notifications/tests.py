from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Notification
from .services import NotificationService

User = get_user_model()


class NotificationServiceTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="StrongPass123!")
        self.user2 = User.objects.create_user(username="user2", password="StrongPass123!")

    def test_notify_user_creates_single_notification(self):
        NotificationService.notify_user(
            self.user1, notification_type="admin_message", title="Hello", body="Welcome!"
        )
        self.assertEqual(Notification.objects.filter(recipient=self.user1).count(), 1)

    def test_broadcast_to_all_reaches_every_active_user(self):
        count = NotificationService.broadcast_to_all(notification_type="promotion", title="Sale!")
        self.assertEqual(count, 2)
        self.assertTrue(Notification.objects.filter(recipient=self.user1).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.user2).exists())

    def test_broadcast_excludes_inactive_users(self):
        self.user2.is_active = False
        self.user2.save()
        count = NotificationService.broadcast_to_all(notification_type="promotion", title="Sale!")
        self.assertEqual(count, 1)

    def test_mark_read_sets_timestamp(self):
        n = NotificationService.notify_user(self.user1, notification_type="admin_message", title="Hi")
        self.assertFalse(n.is_read)
        NotificationService.mark_read(n)
        n.refresh_from_db()
        self.assertTrue(n.is_read)
        self.assertIsNotNone(n.read_at)

    def test_mark_all_read(self):
        NotificationService.notify_user(self.user1, notification_type="admin_message", title="A")
        NotificationService.notify_user(self.user1, notification_type="admin_message", title="B")
        updated = NotificationService.mark_all_read(self.user1)
        self.assertEqual(updated, 2)
        self.assertEqual(Notification.objects.filter(recipient=self.user1, is_read=False).count(), 0)


class NotificationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="StrongPass123!")
        self.other = User.objects.create_user(username="other", password="StrongPass123!")
        NotificationService.notify_user(self.user, notification_type="admin_message", title="For buyer")
        NotificationService.notify_user(self.other, notification_type="admin_message", title="For other")

    def test_list_requires_auth(self):
        response = self.client.get(reverse("notifications:notification-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_only_sees_own_notifications(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("notifications:notification-list"))
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "For buyer")

    def test_unread_count(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("notifications:notification-unread-count"))
        self.assertEqual(response.data["unread_count"], 1)

    def test_mark_read(self):
        self.client.force_authenticate(user=self.user)
        notification = Notification.objects.get(recipient=self.user)
        response = self.client.post(
            reverse("notifications:notification-mark-read", kwargs={"pk": notification.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_read"])

    def test_cannot_mark_others_notification_read(self):
        self.client.force_authenticate(user=self.user)
        others_notification = Notification.objects.get(recipient=self.other)
        response = self.client.post(
            reverse("notifications:notification-mark-read", kwargs={"pk": others_notification.id})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
