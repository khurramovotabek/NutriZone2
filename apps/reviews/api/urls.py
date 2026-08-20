from django.urls import path

from .views import (
    ProductReviewListCreateView,
    ProductReviewSummaryView,
    ReviewDetailView,
    ReviewHelpfulToggleView,
    ReviewReplyCreateView,
    ReviewReportView,
)

app_name = "reviews"

urlpatterns = [
    path("<uuid:pk>/", ReviewDetailView.as_view(), name="review-detail"),
    path("<uuid:pk>/helpful/", ReviewHelpfulToggleView.as_view(), name="review-helpful-toggle"),
    path("<uuid:pk>/report/", ReviewReportView.as_view(), name="review-report"),
    path("<uuid:pk>/replies/", ReviewReplyCreateView.as_view(), name="review-reply-create"),
]

# Nested under products -- included separately in config/api_v1_urls.py
product_review_urlpatterns = [
    path("<slug:product_slug>/reviews/", ProductReviewListCreateView.as_view(), name="product-review-list"),
    path(
        "<slug:product_slug>/reviews/summary/",
        ProductReviewSummaryView.as_view(),
        name="product-review-summary",
    ),
]
