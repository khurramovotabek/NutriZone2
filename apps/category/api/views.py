from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.shared.constants import CACHE_TTL_MEDIUM, LANGUAGES
from apps.shared.exceptions import ServiceError
from apps.shared.i18n import resolve_language
from apps.shared.pagination import LargeResultsPagination
from apps.shared.permissions import IsAdminOrReadOnly, IsAdminUser

from ..models import Category
from ..selectors import (
    categories_with_product_count,
    category_translations_for,
    category_tree_queryset,
    visible_categories_for_user,
)
from ..services import CategoryService
from .serializers import (
    CategoryMiniSerializer,
    CategoryMoveSerializer,
    CategorySerializer,
    CategoryTranslationSerializer,
)


def _tree_cache_key(language: str) -> str:
    # Tree content (names) differs per language, so each language gets its
    # own cache entry -- otherwise the first request's language would get
    # served to everyone until the TTL expires.
    return f"category:tree:v1:{language}"


class CategoryViewSet(viewsets.ModelViewSet):
    """Full CRUD for categories. Public read, admin-only writes.

    Annotates `product_count` (active products only) in a single query so
    the frontend can show counts without extra requests.
    """

    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LargeResultsPagination
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "parent"]
    search_fields = ["translations__name", "translations__description"]
    ordering_fields = ["sort_order", "created_at"]
    ordering = ["sort_order"]

    def get_queryset(self):
        if self.action == "list":
            return visible_categories_for_user(self.request.user)
        return categories_with_product_count()

    def _invalidate_tree_cache(self):
        # Cheap enough at this scale to just clear every language's entry
        # rather than track which languages have ever been cached.
        for code, _ in LANGUAGES:
            cache.delete(_tree_cache_key(code))

    def perform_create(self, serializer):
        serializer.save()
        self._invalidate_tree_cache()

    def perform_update(self, serializer):
        serializer.save()
        self._invalidate_tree_cache()

    def perform_destroy(self, instance):
        instance.delete()
        self._invalidate_tree_cache()

    @action(detail=False, methods=["get"], permission_classes=[IsAdminOrReadOnly])
    def tree(self, request):
        """Full nested category tree for the mega menu / mobile accordion.
        Cached per-language -- this is read constantly (every page's nav)
        and changes rarely (an admin editing categories), so a short TTL
        plus explicit invalidation on write beats recomputing it per
        request."""
        language = resolve_language(request)
        cache_key = _tree_cache_key(language)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        categories = list(category_tree_queryset(request.user))
        tree = CategoryService.build_tree(categories, language)
        cache.set(cache_key, tree, CACHE_TTL_MEDIUM)
        return Response(tree)

    @action(detail=True, methods=["get"], permission_classes=[IsAdminOrReadOnly])
    def breadcrumbs(self, request, slug=None):
        category = get_object_or_404(Category.objects.prefetch_related("translations"), slug=slug)
        ancestors = CategoryService.get_breadcrumbs(category)
        serializer = CategoryMiniSerializer(ancestors + [category], many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def move(self, request, slug=None):
        """Re-parent a category, cascading path/depth to every descendant
        in one pass. Kept separate from the generic update endpoint on
        purpose -- see CategorySerializer.validate()."""
        category = get_object_or_404(Category, slug=slug)
        serializer = CategoryMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            category = CategoryService.reparent(category, serializer.validated_data["parent"])
        except ServiceError as exc:
            return Response({"detail": exc.message, "code": exc.code}, status=status.HTTP_400_BAD_REQUEST)

        self._invalidate_tree_cache()
        return Response(CategorySerializer(category, context={"request": request}).data)


class _CategoryTranslationMixin:
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CategoryTranslationSerializer

    def get_category(self):
        return get_object_or_404(Category, slug=self.kwargs["category_slug"])

    def get_queryset(self):
        return category_translations_for(self.get_category())

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "category": self.get_category()}

    def _invalidate_tree_cache(self):
        for code, _ in LANGUAGES:
            cache.delete(_tree_cache_key(code))

    def perform_create(self, serializer):
        serializer.save(category=self.get_category())
        self._invalidate_tree_cache()

    def perform_update(self, serializer):
        serializer.save()
        self._invalidate_tree_cache()

    def perform_destroy(self, instance):
        instance.delete()
        self._invalidate_tree_cache()


class CategoryTranslationListCreateView(_CategoryTranslationMixin, generics.ListCreateAPIView):
    pass


class CategoryTranslationDetailView(_CategoryTranslationMixin, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "language"
