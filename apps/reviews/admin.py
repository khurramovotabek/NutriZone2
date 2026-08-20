from django.contrib import admin
from django.utils.html import format_html

from .models import Review, ReviewHelpfulVote, ReviewImage, ReviewReply, ReviewReport, ReviewVideo


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0
    fields = ["image", "sort_order"]


class ReviewVideoInline(admin.TabularInline):
    model = ReviewVideo
    extra = 0
    fields = ["video", "thumbnail", "sort_order"]


class ReviewReplyInline(admin.TabularInline):
    """Admin replies, editable directly from the review's page. Saving a
    row here creates a ReviewReply, which fires the "Admin replied to your
    review" notification via apps.reviews.signals -- same as the API path."""

    model = ReviewReply
    extra = 0
    fields = ["admin_user", "message", "created_at"]
    readonly_fields = ["created_at"]
    autocomplete_fields = ["admin_user"]

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields["admin_user"].initial = request.user.pk
        return formset


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "user",
        "rating",
        "verified_badge",
        "helpful_count_display",
        "reported_flag",
        "created_at",
    ]
    list_filter = ["rating", "is_verified_purchase"]
    search_fields = ["product__slug", "product__translations__name", "user__username", "comment"]
    autocomplete_fields = ["product", "user", "order"]
    inlines = [ReviewImageInline, ReviewVideoInline, ReviewReplyInline]

    @admin.display(description="Verified")
    def verified_badge(self, obj):
        if obj.is_verified_purchase:
            return format_html('<span style="color:#9fd42a;">&#10003; Verified</span>')
        return "—"

    @admin.display(description="Helpful")
    def helpful_count_display(self, obj):
        return ReviewHelpfulVote.objects.filter(review=obj).count()

    @admin.display(description="Reported")
    def reported_flag(self, obj):
        count = ReviewReport.objects.filter(review=obj, is_resolved=False).count()
        if count:
            return format_html('<span style="color:#e74c3c;">&#9888; {}</span>', count)
        return "—"


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    """Moderation queue for reported reviews."""

    list_display = ["review", "user", "reason", "is_resolved", "created_at"]
    list_filter = ["reason", "is_resolved"]
    list_editable = ["is_resolved"]
    autocomplete_fields = ["review", "user"]
    search_fields = ["review__product__slug", "user__username", "comment"]
