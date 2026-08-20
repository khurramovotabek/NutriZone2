from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.orders.models import Order
from apps.products.models import Product
from apps.shared.models import BaseModel, SortableModel


class Review(BaseModel):
    """A customer's rating + written review of a product.

    Only customers who have a DELIVERED (Order.Status.ACCEPTED) order
    containing the product may create one -- enforced in services.py, not
    here, so the rule stays testable independent of the ORM constraint
    layer. One review per (user, product): editing replaces it rather than
    stacking duplicates.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
        help_text="The delivered order that verified this purchase, if any.",
    )

    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    is_verified_purchase = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["product", "user"], name="one_review_per_user_per_product")
        ]
        indexes = [models.Index(fields=["product", "-created_at"])]

    def __str__(self):
        return f"{self.user} rated {self.product} {self.rating}/5"


class ReviewImage(BaseModel, SortableModel):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="reviews/")

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"Image for review {self.review_id}"


class ReviewVideo(BaseModel, SortableModel):
    """Kept as a separate model from ReviewImage (rather than a unified
    'ReviewMedia' with a type field) so existing ReviewImage code --
    already shipped, tested, and wired into serializers/admin -- doesn't
    need a disruptive rename. Same purpose (customer-uploaded proof), same
    ownership (belongs to one Review), different validation (video file
    types, larger size ceiling) which reads more clearly as its own model."""

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="videos")
    video = models.FileField(upload_to="reviews/videos/")
    thumbnail = models.ImageField(upload_to="reviews/video_thumbnails/", blank=True, null=True)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"Video for review {self.review_id}"


class ReviewReply(BaseModel):
    """An admin's reply to a customer's review. Modeled as a FK (not
    OneToOne) so a conversation can have more than one admin follow-up,
    even though the common case is a single reply."""

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="replies")
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="review_replies"
    )
    message = models.TextField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply to review {self.review_id}"


class ReviewHelpfulVote(BaseModel):
    """One row per (review, user) marking that review as helpful --
    prevents a single user from inflating the count by repeat-clicking."""

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="helpful_votes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_helpful_votes"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["review", "user"], name="one_helpful_vote_per_user_per_review")
        ]

    def __str__(self):
        return f"{self.user} found review {self.review_id} helpful"


class ReviewReport(BaseModel):
    """A user flagging a review as inappropriate/spam for admin attention.
    One report per (review, user) -- repeated clicking doesn't spam
    duplicate reports."""

    class Reason(models.TextChoices):
        SPAM = "spam", "Spam or advertising"
        OFFENSIVE = "offensive", "Offensive content"
        FAKE = "fake", "Suspected fake review"
        OTHER = "other", "Other"

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="reports")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_reports"
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    comment = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["review", "user"], name="one_report_per_user_per_review")
        ]

    def __str__(self):
        return f"Report on review {self.review_id} ({self.reason})"
