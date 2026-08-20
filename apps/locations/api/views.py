from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from apps.shared.pagination import LargeResultsPagination
from apps.shared.permissions import IsAdminOrReadOnly

from ..selectors import visible_cities, visible_countries, visible_regions
from .serializers import CitySerializer, CountrySerializer, RegionSerializer


class CountryViewSet(viewsets.ModelViewSet):
    serializer_class = CountrySerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LargeResultsPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering = ["name"]

    def get_queryset(self):
        return visible_countries(self.request.user)


class RegionViewSet(viewsets.ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LargeResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["country"]
    search_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        return visible_regions(self.request.user)


class CityViewSet(viewsets.ModelViewSet):
    serializer_class = CitySerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LargeResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["region"]
    search_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        return visible_cities(self.request.user)
