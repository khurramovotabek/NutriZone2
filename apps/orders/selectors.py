"""Read-query construction for orders."""

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet

from .models import Order


def orders_base_queryset() -> QuerySet[Order]:
    return Order.objects.prefetch_related("items").select_related("country", "region", "city", "user")


def orders_visible_to_user(user: AbstractBaseUser) -> QuerySet[Order]:
    """Staff see every order; authenticated customers see only their own;
    anonymous callers see nothing (they can only create + get the one order
    back from the checkout response itself)."""
    qs = orders_base_queryset()
    if user.is_authenticated and user.is_staff:
        return qs
    if user.is_authenticated:
        return qs.filter(user=user)
    return qs.none()
