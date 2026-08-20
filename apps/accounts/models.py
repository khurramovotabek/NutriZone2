import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model.

    Covers both administrators (is_staff=True) and registered customers.
    Guest checkout does NOT require a User record -- Order stores its own
    contact-info snapshot regardless of whether the customer is logged in.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, blank=True, db_index=True)
    telegram_username = models.CharField(max_length=64, blank=True)
    is_customer = models.BooleanField(
        default=True,
        help_text="False for internal/admin-only accounts that aren't shoppers.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.username
