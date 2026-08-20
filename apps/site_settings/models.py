from django.core.exceptions import ValidationError
from django.db import models

from apps.shared.models import BaseModel


class SiteSettings(BaseModel):
    """Singleton row holding storefront-wide configuration.

    Enforced as a singleton via clean()/save() rather than a hardcoded
    pk, so it still works cleanly with the shared UUID BaseModel.
    """

    site_name = models.CharField(max_length=150, default="NutriZone")
    currency = models.CharField(max_length=10, default="UZS")
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    telegram_link = models.URLField(blank=True)
    instagram_link = models.URLField(blank=True)
    address = models.TextField(blank=True)
    maintenance_mode = models.BooleanField(default=False)
    logo = models.ImageField(upload_to="settings/", blank=True, null=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name

    def clean(self):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError("Site settings already exist. Edit the existing record instead.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteSettings":
        obj = cls.objects.first()
        return obj if obj else cls.objects.create()
