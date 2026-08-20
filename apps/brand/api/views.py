from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, viewsets

from apps.shared.pagination import LargeResultsPagination
from apps.shared.permissions import IsAdminOrReadOnly

from ..models import Brand
from ..selectors import brand_translations_for, brands_with_product_count, visible_brands_for_user
from .serializers import BrandSerializer, BrandTranslationSerializer


class BrandViewSet(viewsets.ModelViewSet):
    serializer_class = BrandSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LargeResultsPagination
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["name", "translations__description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        if self.action == "list":
            return visible_brands_for_user(self.request.user)
        return brands_with_product_count()


class _BrandTranslationMixin:
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = BrandTranslationSerializer

    def get_brand(self):
        return get_object_or_404(Brand, slug=self.kwargs["brand_slug"])

    def get_queryset(self):
        return brand_translations_for(self.get_brand())

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "brand": self.get_brand()}

    def perform_create(self, serializer):
        serializer.save(brand=self.get_brand())


class BrandTranslationListCreateView(_BrandTranslationMixin, generics.ListCreateAPIView):
    pass


class BrandTranslationDetailView(_BrandTranslationMixin, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "language"
