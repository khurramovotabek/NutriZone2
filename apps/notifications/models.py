from django.conf import settings
from django.db import models

from apps.shared.models import BaseModel


class Notification(BaseModel):
    """A single notification for a single recipient.

    "Broadcast to all users" / "send to selected users" are NOT modeled as
    a separate one-row-many-recipients concept -- NotificationService bulk-
    creates one row per recipient instead. That keeps read/unread state
    (which is inherently per-user) simple: no join table, no special-casing
    "is this the broadcast version or my personal copy."
    """

    class NotificationType(models.TextChoices):
        ORDER_UPDATE = "order_update", "Order update"
        PROMOTION = "promotion", "Promotion"
        DISCOUNT = "discount", "Discount"
        ADMIN_MESSAGE = "admin_message", "Admin message"
        REVIEW_REPLY = "review_reply", "Review reply"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, db_index=True)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    link_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Frontend-relative path to deep-link to, e.g. a product's reviews.",
    )
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} -> {self.recipient}"
