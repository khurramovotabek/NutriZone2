"""Read-query construction for the product catalog.

Keeping these out of views.py means the "what does the DB actually get
asked" logic is testable and reusable independent of HTTP concerns, and
views.py stays a thin translation layer between request params and these
functions.
"""

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Avg, Count, FloatField, IntegerField, OuterRef, Prefetch, QuerySet, Subquery
from django.db.models.functions import Coalesce

from apps.reviews.models import Review

from .models import Product, ProductImage, ProductSpecification, ProductVariant
from .services import ProductService


def _rating_average_subquery():
    return (
        Review.objects.filter(product=OuterRef("pk"))
        .values("product")
        .annotate(avg=Avg("rating"))
        .values("avg")
    )


def _rating_count_subquery():
    return (
        Review.objects.filter(product=OuterRef("pk"))
        .values("product")
        .annotate(cnt=Count("id"))
        .values("cnt")
    )


def product_catalog_base_queryset() -> QuerySet[Product]:
    """The one query shape used by both list and detail: joins + prefetches
    everything a product page needs so the API can serve it in one request.

    Rating aggregates are computed via correlated Subquery (not a plain
    .annotate(Avg(...)) join) specifically so they stay correct alongside
    the variants/images/specifications prefetches and the price-based
    ordering below -- a plain join-based aggregate here would silently
    inflate/deflate once combined with another to-many join.
    """
    return (
        Product.objects.select_related("category", "brand")
        .annotate(
            rating_average=Subquery(_rating_average_subquery(), output_field=FloatField()),
            rating_count=Coalesce(Subquery(_rating_count_subquery(), output_field=IntegerField()), 0),
        )
        .prefetch_related(
            "translations",
            "category__translations",
            "brand__translations",
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_primary", "sort_order")),
            Prefetch("variants", queryset=ProductVariant.objects.order_by("-is_default", "price")),
            Prefetch("specifications", queryset=ProductSpecification.objects.order_by("sort_order")),
        )
    )


_SORT_MAP = {
    "newest": "-created_at",
    "oldest": "created_at",
    "price_low": "variants__price",
    "price_high": "-variants__price",
}


def visible_products_for_user(user: AbstractBaseUser | None) -> QuerySet[Product]:
    """Staff see everything (including inactive products for QA); everyone
    else only sees active products."""
    qs = product_catalog_base_queryset()
    if not (user and user.is_authenticated and user.is_staff):
        qs = qs.filter(is_active=True)
    return qs


def filter_product_catalog(
    qs: QuerySet[Product],
    *,
    search: str | None = None,
    availability: str | None = None,
    sort: str | None = None,
) -> QuerySet[Product]:
    if search:
        qs = ProductService.search(qs, search)
    if availability:
        qs = ProductService.filter_by_availability(qs, availability)
    if sort in _SORT_MAP:
        qs = qs.order_by(_SORT_MAP[sort]).distinct()
    return qs


def product_translations_for(product: Product):
    return product.translations.order_by("language")
