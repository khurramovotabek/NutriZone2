from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BrandTranslationDetailView, BrandTranslationListCreateView, BrandViewSet

app_name = "brands"

router = DefaultRouter()
router.register("", BrandViewSet, basename="brand")

urlpatterns = [
    path(
        "<slug:brand_slug>/translations/",
        BrandTranslationListCreateView.as_view(),
        name="brand-translation-list",
    ),
    path(
        "<slug:brand_slug>/translations/<str:language>/",
        BrandTranslationDetailView.as_view(),
        name="brand-translation-detail",
    ),
] + router.urls
