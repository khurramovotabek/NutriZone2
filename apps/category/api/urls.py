from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CategoryTranslationDetailView, CategoryTranslationListCreateView, CategoryViewSet

app_name = "categories"

router = DefaultRouter()
router.register("", CategoryViewSet, basename="category")

urlpatterns = [
    path(
        "<slug:category_slug>/translations/",
        CategoryTranslationListCreateView.as_view(),
        name="category-translation-list",
    ),
    path(
        "<slug:category_slug>/translations/<str:language>/",
        CategoryTranslationDetailView.as_view(),
        name="category-translation-detail",
    ),
] + router.urls
