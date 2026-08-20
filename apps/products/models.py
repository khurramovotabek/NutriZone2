from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.brand.models import Brand
from apps.category.models import Category
from apps.shared.constants import LANGUAGES
from apps.shared.models import BaseModel, SortableModel


class Product(BaseModel):
    """Translated content (name, description, SEO metadata) lives on
    ProductTranslation, one row per language. `slug` stays here and is NOT
    translated -- same slug is reused across all locale-prefixed frontend
    URLs. Since there's no `name` on this model anymore, slug is a
    required, manually-set field rather than auto-derived."""

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")

    slug = models.SlugField(max_length=280, unique=True)

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "-created_at"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["brand", "is_active"]),
        ]

    def __str__(self):
        return self.slug

    @property
    def min_price(self):
        """Lowest active variant price, used for card display. Prefer the
        annotated queryset value when available to avoid extra queries."""
        if hasattr(self, "_min_price"):
            return self._min_price
        # Deliberately `self.variants.all()` + Python filtering, NOT
        # `self.variants.filter(...)` -- prefetch_related's cache only
        # backs unmodified `.all()` access; any .filter()/.exclude() chained
        # on the manager always re-queries the DB, silently defeating the
        # whole point of prefetching (this was a real N+1 bug here before).
        active_prices = [v.price for v in self.variants.all() if v.status == ProductVariant.Status.ACTIVE]
        return min(active_prices) if active_prices else None

    @property
    def is_in_stock(self):
        if hasattr(self, "_in_stock"):
            return self._in_stock
        return any(v.status == ProductVariant.Status.ACTIVE and v.quantity > 0 for v in self.variants.all())


class ProductTranslation(BaseModel):
    """One row per (product, language). See apps.shared.i18n for how these
    get resolved with fallback (requested -> en -> uz)."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=5, choices=LANGUAGES)

    name = models.CharField(max_length=255)
    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["language"]
        constraints = [
            models.UniqueConstraint(fields=["product", "language"], name="unique_product_translation")
        ]
        indexes = [
            models.Index(fields=["language"]),
            models.Index(fields=["product", "language"]),
        ]

    def __str__(self):
        return f"{self.product_id} [{self.language}] {self.name}"


class ProductImage(BaseModel, SortableModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-is_primary", "sort_order"]

    def __str__(self):
        return f"{self.product.slug} image ({'primary' if self.is_primary else self.sort_order})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_primary:
            # Ensure only one primary image per product.
            ProductImage.objects.filter(product=self.product).exclude(pk=self.pk).update(is_primary=False)


class ProductVariant(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")

    sku = models.CharField(max_length=100, unique=True, db_index=True)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True, db_index=True)

    price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    old_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    quantity = models.PositiveIntegerField(default=0)

    weight = models.CharField(max_length=50, blank=True, help_text="e.g. 300g, 500g, 1kg")
    flavor = models.CharField(max_length=100, blank=True, help_text="e.g. Chocolate, Vanilla")

    is_default = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    class Meta:
        ordering = ["-is_default", "price"]
        indexes = [models.Index(fields=["product", "status"])]

    def __str__(self):
        return f"{self.product.slug} - {self.sku}"

    @property
    def is_in_stock(self):
        return self.status == self.Status.ACTIVE and self.quantity > 0

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return round((1 - (self.price / self.old_price)) * 100)
        return 0

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            ProductVariant.objects.filter(product=self.product).exclude(pk=self.pk).update(is_default=False)


class ProductSpecification(BaseModel, SortableModel):
    """Fully dynamic key/value spec, e.g. Protein -> 24g, Calories -> 120 kcal."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specifications")
    label = models.CharField(max_length=150)
    value = models.CharField(max_length=255)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.label}: {self.value}"
