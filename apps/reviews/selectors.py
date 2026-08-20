"""Read-query construction for reviews."""

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Count, Prefetch, QuerySet

from apps.orders.models import Order

from .models import Review, ReviewHelpfulVote, ReviewReply


def reviews_for_product(product_id) -> QuerySet[Review]:
    return (
        Review.objects.filter(product_id=product_id)
        .select_related("user")
        .annotate(helpful_count=Count("helpful_votes", distinct=True))
        .prefetch_related(
            "images",
            "videos",
            Prefetch("replies", queryset=ReviewReply.objects.select_related("admin_user")),
        )
        .order_by("-created_at")
    )


def user_has_purchased(user: AbstractBaseUser, product_id) -> bool:
    """True if the user has at least one DELIVERED order containing this product."""
    if not user or not user.is_authenticated:
        return False
    return Order.objects.filter(
        user=user,
        status=Order.Status.ACCEPTED,
        items__variant__product_id=product_id,
    ).exists()


def helpful_review_ids_for_user(user: AbstractBaseUser, review_ids) -> set:
    """Which of these reviews has this user already marked helpful --
    one query regardless of how many reviews are being serialized."""
    if not user or not user.is_authenticated:
        return set()

    return set(
        ReviewHelpfulVote.objects.filter(user=user, review_id__in=review_ids).values_list(
            "review_id", flat=True
        )
    )


def rating_summary(product_id) -> dict:
    """Average rating, total count, and star-distribution percentages for a product."""
    counts = dict(
        Review.objects.filter(product_id=product_id).values_list("rating").annotate(count=Count("id"))
    )
    total = sum(counts.values())
    average = round(sum(stars * count for stars, count in counts.items()) / total, 2) if total else None
    distribution = {
        str(stars): round((counts.get(stars, 0) / total) * 100) if total else 0 for stars in range(5, 0, -1)
    }
    return {"average": average, "total": total, "distribution": distribution}
