"""Read-query construction for categories."""

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Count, Prefetch, Q, QuerySet

from .models import Category, CategoryTranslation


def categories_with_product_count() -> QuerySet[Category]:
    return (
        Category.objects.select_related("parent")
        .prefetch_related("translations")
        .annotate(product_count=Count("products", filter=Q(products__is_active=True), distinct=True))
    )


def visible_categories_for_user(user: AbstractBaseUser | None) -> QuerySet[Category]:
    qs = categories_with_product_count()
    if not (user and user.is_authenticated and user.is_staff):
        qs = qs.filter(is_active=True)
    return qs


def category_tree_queryset(user: AbstractBaseUser | None = None) -> QuerySet[Category]:
    """All categories in an order that lets build_tree() append children in
    the right sequence without a second sort: parents before children,
    siblings by sort_order. Translations are prefetched so build_tree()'s
    per-node get_translation() call never issues its own query."""
    qs = Category.objects.prefetch_related(
        Prefetch("translations", queryset=CategoryTranslation.objects.all())
    )
    if not (user and user.is_authenticated and user.is_staff):
        qs = qs.filter(is_active=True)
    return qs.order_by("depth", "sort_order")


def category_translations_for(category: Category) -> QuerySet[CategoryTranslation]:
    return CategoryTranslation.objects.filter(category=category).order_by("language")
