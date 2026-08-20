from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import Product
from apps.shared.exceptions import ServiceError
from apps.shared.pagination import StandardResultsPagination
from apps.shared.permissions import IsAdminUser

from ..models import Review, ReviewImage, ReviewVideo
from ..permissions import IsOwnerOrAdmin
from ..selectors import helpful_review_ids_for_user, rating_summary, reviews_for_product
from ..services import ReviewReplyService, ReviewService
from .serializers import (
    RatingSummarySerializer,
    ReviewCreateSerializer,
    ReviewReplyCreateSerializer,
    ReviewReplySerializer,
    ReviewReportCreateSerializer,
    ReviewSerializer,
    ReviewUpdateSerializer,
)


class ProductReviewListCreateView(generics.ListCreateAPIView):
    """GET: paginated reviews for a product (public).
    POST: create a review for this product (authenticated + verified purchase only).
    """

    serializer_class = ReviewSerializer
    pagination_class = StandardResultsPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_product(self):
        return get_object_or_404(Product, slug=self.kwargs["product_slug"])

    def get_queryset(self):
        return reviews_for_product(self.get_product().id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        review_ids = [r.id for r in self.get_queryset()]
        context["helpful_review_ids"] = helpful_review_ids_for_user(self.request.user, review_ids)
        return context

    def create(self, request, *args, **kwargs):
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = self.get_product()

        try:
            review = ReviewService.create_review(
                user=request.user,
                product=product,
                rating=serializer.validated_data["rating"],
                comment=serializer.validated_data.get("comment", ""),
            )
        except ServiceError as exc:
            return Response({"detail": exc.message, "code": exc.code}, status=status.HTTP_400_BAD_REQUEST)

        for image in serializer.validated_data.get("images", []):
            ReviewImage.objects.create(review=review, image=image)
        for video in serializer.validated_data.get("videos", []):
            ReviewVideo.objects.create(review=review, video=video)

        return Response(
            ReviewSerializer(review, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


class ProductReviewSummaryView(APIView):
    """GET: average rating, total count, and star-distribution for a product."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        return Response(RatingSummarySerializer(rating_summary(product.id)).data)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Owner (or admin) can edit/delete their own review."""

    queryset = Review.objects.select_related("user").prefetch_related("images", "videos", "replies")
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return ReviewUpdateSerializer
        return ReviewSerializer

    def update(self, request, *args, **kwargs):
        review = self.get_object()
        serializer = ReviewUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = ReviewService.update_review(review, **serializer.validated_data)
        return Response(ReviewSerializer(updated).data)


class ReviewHelpfulToggleView(APIView):
    """POST toggles whether the current user has marked this review helpful."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        marked, count = ReviewService.toggle_helpful(review, request.user)
        return Response({"is_marked_helpful_by_me": marked, "helpful_count": count})


class ReviewReportView(APIView):
    """POST flags a review as inappropriate/spam for admin attention."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        serializer = ReviewReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            ReviewService.report_review(review, request.user, **serializer.validated_data)
        except ServiceError as exc:
            return Response({"detail": exc.message, "code": exc.code}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"detail": "Review reported. Our team will take a look."}, status=status.HTTP_201_CREATED
        )


class ReviewReplyCreateView(APIView):
    """POST: admin-only reply to a review, via the API (the same event also
    happens through the Django admin inline -- see reviews/signals.py for
    the notification, which fires either way)."""

    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        serializer = ReviewReplyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reply = ReviewReplyService.add_reply(review, request.user, serializer.validated_data["message"])
        return Response(ReviewReplySerializer(reply).data, status=status.HTTP_201_CREATED)
