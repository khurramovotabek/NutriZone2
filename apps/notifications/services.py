from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Notification

User = get_user_model()


class NotificationService:
    @staticmethod
    def notify_user(
        user, *, notification_type: str, title: str, body: str = "", link_path: str = ""
    ) -> Notification:
        return Notification.objects.create(
            recipient=user,
            notification_type=notification_type,
            title=title,
            body=body,
            link_path=link_path,
        )

    @staticmethod
    def notify_users(
        users, *, notification_type: str, title: str, body: str = "", link_path: str = ""
    ) -> int:
        """Send the same notification to a specific set of users. Returns
        the number created."""
        notifications = [
            Notification(
                recipient=user,
                notification_type=notification_type,
                title=title,
                body=body,
                link_path=link_path,
            )
            for user in users
        ]
        created = Notification.objects.bulk_create(notifications)
        return len(created)

    @staticmethod
    def broadcast_to_all(*, notification_type: str, title: str, body: str = "", link_path: str = "") -> int:
        """Send to every active customer account."""
        return NotificationService.notify_users(
            User.objects.filter(is_active=True),
            notification_type=notification_type,
            title=title,
            body=body,
            link_path=link_path,
        )

    @staticmethod
    def mark_read(notification: Notification) -> Notification:
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at", "updated_at"])
        return notification

    @staticmethod
    def mark_all_read(user) -> int:
        return Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
