"""Read-query construction for brands."""

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Count, Q, QuerySet

from .models import Brand


def brands_with_product_count() -> QuerySet[Brand]:
    return (
        Brand.objects.select_related("country")
        .prefetch_related("translations")
        .annotate(product_count=Count("products", filter=Q(products__is_active=True), distinct=True))
    )


def visible_brands_for_user(user: AbstractBaseUser | None) -> QuerySet[Brand]:
    qs = brands_with_product_count()
    if not (user and user.is_authenticated and user.is_staff):
        qs = qs.filter(is_active=True)
    return qs


def brand_translations_for(brand: Brand):
    return brand.translations.order_by("language")
