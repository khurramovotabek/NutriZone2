from django.db import transaction

from apps.orders.models import Order
from apps.shared.exceptions import ServiceError

from .models import Review, ReviewHelpfulVote, ReviewReply, ReviewReport
from .selectors import user_has_purchased


class ReviewService:
    @staticmethod
    @transaction.atomic
    def create_review(*, user, product, rating: int, comment: str = "") -> Review:
        if Review.objects.filter(product=product, user=user).exists():
            raise ServiceError(
                "You've already reviewed this product. Edit your existing review instead.",
                code="duplicate_review",
            )
        if not user_has_purchased(user, product.id):
            raise ServiceError(
                "Only customers with a delivered order for this product can leave a review.",
                code="purchase_not_verified",
            )

        verifying_order = (
            Order.objects.filter(user=user, status=Order.Status.ACCEPTED, items__variant__product=product)
            .order_by("-created_at")
            .first()
        )

        return Review.objects.create(
            product=product,
            user=user,
            order=verifying_order,
            rating=rating,
            comment=comment,
            is_verified_purchase=True,
        )

    @staticmethod
    def update_review(review: Review, *, rating: int | None = None, comment: str | None = None) -> Review:
        if rating is not None:
            review.rating = rating
        if comment is not None:
            review.comment = comment
        review.save(update_fields=["rating", "comment", "updated_at"])
        return review

    @staticmethod
    def toggle_helpful(review: Review, user) -> tuple[bool, int]:
        """Returns (now_marked_helpful, total_helpful_count)."""
        vote, created = ReviewHelpfulVote.objects.get_or_create(review=review, user=user)
        if not created:
            vote.delete()
            marked = False
        else:
            marked = True
        count = ReviewHelpfulVote.objects.filter(review=review).count()
        return marked, count

    @staticmethod
    def report_review(review: Review, user, *, reason: str, comment: str = "") -> ReviewReport:
        if ReviewReport.objects.filter(review=review, user=user).exists():
            raise ServiceError("You've already reported this review.", code="duplicate_report")
        return ReviewReport.objects.create(review=review, user=user, reason=reason, comment=comment)


class ReviewReplyService:
    @staticmethod
    def add_reply(review: Review, admin_user, message: str) -> ReviewReply:
        """Admin reply to a customer's review.

        Notification-on-reply is handled by a post_save signal
        (apps.reviews.signals), not here -- replies can also be created
        directly through the Django admin inline, which bypasses this
        service entirely. A signal guarantees the notification fires
        regardless of which path created the row; duplicating that logic
        here as well would risk a double notification.
        """
        return ReviewReply.objects.create(review=review, admin_user=admin_user, message=message)
