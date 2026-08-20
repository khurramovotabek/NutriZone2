"""Read-query helpers for carts.

Cart resolution (guest vs authenticated) is business logic that belongs in
services.py (it decides *which* cart to use, including creating one) --
this file only holds pure read queries used alongside that.
"""

from django.db.models import QuerySet

from .models import Cart


def cart_with_items(cart_id) -> QuerySet[Cart]:
    return Cart.objects.filter(id=cart_id).prefetch_related(
        "items__variant__product__images",
        "items__variant__product__translations",
    )
