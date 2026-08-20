"""Read-query construction for notifications."""

from django.db.models import QuerySet

from .models import Notification


def notifications_for_user(user) -> QuerySet[Notification]:
    return Notification.objects.filter(recipient=user)


def unread_count(user) -> int:
    return Notification.objects.filter(recipient=user, is_read=False).count()
