from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, viewsets

from apps.shared.pagination import StandardResultsPagination
from apps.shared.permissions import IsAdminOrReadOnly

from ..models import Product, ProductImage, ProductSpecification, ProductVariant
from ..selectors import filter_product_catalog, product_translations_for, visible_products_for_user
from .filters import ProductFilter
from .serializers import (
    ProductDetailSerializer,
    ProductImageSerializer,
    ProductListSerializer,
    ProductSpecificationSerializer,
    ProductTranslationSerializer,
    ProductVariantSerializer,
    ProductWriteSerializer,
)


class ProductViewSet(viewsets.ModelViewSet):
    """Public catalog + admin management for products.

    - list: paginated, filterable, searchable, orderable catalog
    - retrieve: full product detail in a single request
    - create/update/destroy: admin only
    """

    lookup_field = "slug"
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = []  # custom search handled in get_queryset via selectors.filter_product_catalog
    ordering_fields = ["created_at"]  # "name" isn't orderable -- it's translated, use ?sort= instead
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = visible_products_for_user(self.request.user)
        return filter_product_catalog(
            qs,
            search=self.request.query_params.get("search"),
            availability=self.request.query_params.get("availability"),
            sort=self.request.query_params.get("sort"),
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductWriteSerializer


class _ProductScopedMixin:
    """Shared helper: resolve the parent product from the URL and scope
    the nested queryset to it. Admin-only writes, public reads."""

    permission_classes = [IsAdminOrReadOnly]

    def get_product(self):
        return get_object_or_404(Product, slug=self.kwargs["product_slug"])

    def get_queryset(self):
        return self.queryset_model.objects.filter(product=self.get_product())

    def perform_create(self, serializer):
        serializer.save(product=self.get_product())


# ---- Product Images ----------------------------------------------------


class ProductImageListCreateView(_ProductScopedMixin, generics.ListCreateAPIView):
    serializer_class = ProductImageSerializer
    queryset_model = ProductImage


class ProductImageDetailView(_ProductScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductImageSerializer
    queryset_model = ProductImage


# ---- Product Variants ---------------------------------------------------


class ProductVariantListCreateView(_ProductScopedMixin, generics.ListCreateAPIView):
    serializer_class = ProductVariantSerializer
    queryset_model = ProductVariant


class ProductVariantDetailView(_ProductScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductVariantSerializer
    queryset_model = ProductVariant


# ---- Product Specifications ---------------------------------------------


class ProductSpecificationListCreateView(_ProductScopedMixin, generics.ListCreateAPIView):
    serializer_class = ProductSpecificationSerializer
    queryset_model = ProductSpecification


class ProductSpecificationDetailView(_ProductScopedMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSpecificationSerializer
    queryset_model = ProductSpecification


# ---- Product Translations -------------------------------------------------


class _ProductTranslationMixin:
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = ProductTranslationSerializer

    def get_product(self):
        return get_object_or_404(Product, slug=self.kwargs["product_slug"])

    def get_queryset(self):
        return product_translations_for(self.get_product())

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "product": self.get_product()}

    def perform_create(self, serializer):
        serializer.save(product=self.get_product())


class ProductTranslationListCreateView(_ProductTranslationMixin, generics.ListCreateAPIView):
    pass


class ProductTranslationDetailView(_ProductTranslationMixin, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "language"
