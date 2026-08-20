from django.db import models

from apps.shared.constants import LANGUAGES
from apps.shared.models import BaseModel, SortableModel


class Category(BaseModel, SortableModel):
    """A node in the category tree.

    Tree structure is adjacency list (`parent`) for edits, plus a
    materialized `path` (ancestor ids joined by "/") for fast descendant/
    ancestor queries without recursive SQL. See CategoryService for the
    invariant-preserving operations (create under parent, move/reparent).
    Never mutate `path`/`depth` directly -- always go through the service
    or `save()`, both of which recompute them from `parent`.

    Translated content (name, description, SEO metadata) lives on
    CategoryTranslation, one row per language -- see that model's
    docstring. `slug` stays here and is NOT translated: URLs are
    locale-prefixed on the frontend (/ru/products?category=whey-protein),
    not per-language-sluggified, so the same slug is used across all
    languages. Since there's no `name` on this model anymore, slug is a
    required, manually-set field rather than auto-derived.
    """

    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children"
    )

    slug = models.SlugField(max_length=170, unique=True)
    icon = models.CharField(
        max_length=64,
        blank=True,
        help_text="Icon identifier for the mega menu, e.g. a lucide-react icon name.",
    )
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Materialized path, e.g. "<root_id>/<child_id>/" -- always ends with a
    # trailing slash so prefix matching (path__startswith) never false-
    # positives on a sibling whose id happens to share a prefix.
    path = models.CharField(max_length=800, editable=False, db_index=True, blank=True)
    depth = models.PositiveSmallIntegerField(default=0, editable=False, db_index=True)

    class Meta:
        ordering = ["sort_order"]
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
            models.Index(fields=["path"]),
            models.Index(fields=["parent", "sort_order"]),
        ]

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        # self.id is already populated here (BaseModel's UUID default is
        # assigned in Python before INSERT), so path can be computed on
        # first save without a second round-trip.
        if self.parent_id:
            self.depth = self.parent.depth + 1
            self.path = f"{self.parent.path}{self.id}/"
        else:
            self.depth = 0
            self.path = f"{self.id}/"
        super().save(*args, **kwargs)


class CategoryTranslation(BaseModel):
    """One row per (category, language). See apps.shared.i18n for how these
    get resolved with fallback (requested -> en -> uz)."""

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=5, choices=LANGUAGES)

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["language"]
        constraints = [
            models.UniqueConstraint(fields=["category", "language"], name="unique_category_translation")
        ]
        indexes = [
            models.Index(fields=["language"]),
            models.Index(fields=["category", "language"]),
        ]

    def __str__(self):
        return f"{self.category_id} [{self.language}] {self.name}"
