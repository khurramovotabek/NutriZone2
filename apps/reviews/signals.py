"""Signal handlers for the reviews domain.

The one wired-up signal: notify a review's author when an admin reply is
created. Deliberately a signal rather than a service-layer call -- replies
can be created either through the API (ReviewReplyService.add_reply) or
directly via the Django admin's inline formset (which never touches that
service), so a signal is the only place that reliably sees both paths.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notifications.services import NotificationService
from apps.shared.i18n import get_translation

from .models import ReviewReply


@receiver(post_save, sender=ReviewReply)
def notify_on_review_reply(sender, instance: ReviewReply, created: bool, **kwargs):
    if not created:
        return

    review = instance.review
    resolved = get_translation(review.product, "en")
    product_name = resolved.translation.name if resolved.translation else review.product.slug

    NotificationService.notify_user(
        review.user,
        notification_type="review_reply",
        title="Admin replied to your review",
        body=f"Admin replied to your review of {product_name}.",
        link_path=f"/products/{review.product.slug}#reviews",
    )
