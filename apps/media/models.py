from django.conf import settings
from django.db import models

from apps.shared.models import BaseModel


def media_upload_path(instance, filename):
    folder = instance.folder or "misc"
    return f"media/{folder}/{filename}"


class MediaFile(BaseModel):
    """General-purpose uploaded file, independent of any specific product.

    Used for things like homepage banners, brand assets, or admin-uploaded
    content that doesn't belong to a single product's image gallery.
    """

    file = models.FileField(upload_to=media_upload_path)
    folder = models.CharField(max_length=100, blank=True, default="misc", db_index=True)
    original_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(default=0, help_text="File size in bytes")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_media",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["folder", "-created_at"])]

    def __str__(self):
        return self.original_name or self.file.name

    def save(self, *args, **kwargs):
        if self.file and not self.size:
            self.size = self.file.size
        if self.file and not self.original_name:
            self.original_name = self.file.name
        super().save(*args, **kwargs)
