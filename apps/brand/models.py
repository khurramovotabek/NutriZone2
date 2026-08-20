from django.db import models
from django.utils.text import slugify

from apps.locations.models import Country
from apps.shared.constants import LANGUAGES
from apps.shared.models import BaseModel


class Brand(BaseModel):
    """`name` is a proper noun (e.g. "Optimum Nutrition") and is
    deliberately NOT translated. `description` is, and lives on
    BrandTranslation -- see that model's docstring."""

    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    logo = models.ImageField(upload_to="brands/", blank=True, null=True)
    website = models.URLField(blank=True)
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="brands",
        help_text="Country the brand originates from.",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["is_active"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BrandTranslation(BaseModel):
    """One row per (brand, language) -- only `description` is translated,
    see Brand's docstring for why `name` isn't."""

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=5, choices=LANGUAGES)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["language"]
        constraints = [models.UniqueConstraint(fields=["brand", "language"], name="unique_brand_translation")]
        indexes = [
            models.Index(fields=["language"]),
            models.Index(fields=["brand", "language"]),
        ]

    def __str__(self):
        return f"{self.brand_id} [{self.language}]"
