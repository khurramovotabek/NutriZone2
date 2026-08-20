from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ProductImageDetailView,
    ProductImageListCreateView,
    ProductSpecificationDetailView,
    ProductSpecificationListCreateView,
    ProductTranslationDetailView,
    ProductTranslationListCreateView,
    ProductVariantDetailView,
    ProductVariantListCreateView,
    ProductViewSet,
)

app_name = "products"

router = DefaultRouter()
router.register("", ProductViewSet, basename="product")

urlpatterns = [
    path(
        "<slug:product_slug>/images/",
        ProductImageListCreateView.as_view(),
        name="product-image-list",
    ),
    path(
        "<slug:product_slug>/images/<uuid:pk>/",
        ProductImageDetailView.as_view(),
        name="product-image-detail",
    ),
    path(
        "<slug:product_slug>/variants/",
        ProductVariantListCreateView.as_view(),
        name="product-variant-list",
    ),
    path(
        "<slug:product_slug>/variants/<uuid:pk>/",
        ProductVariantDetailView.as_view(),
        name="product-variant-detail",
    ),
    path(
        "<slug:product_slug>/specifications/",
        ProductSpecificationListCreateView.as_view(),
        name="product-specification-list",
    ),
    path(
        "<slug:product_slug>/specifications/<uuid:pk>/",
        ProductSpecificationDetailView.as_view(),
        name="product-specification-detail",
    ),
    path(
        "<slug:product_slug>/translations/",
        ProductTranslationListCreateView.as_view(),
        name="product-translation-list",
    ),
    path(
        "<slug:product_slug>/translations/<str:language>/",
        ProductTranslationDetailView.as_view(),
        name="product-translation-detail",
    ),
] + router.urls
