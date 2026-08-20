from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from apps.shared.pagination import StandardResultsPagination
from apps.shared.permissions import IsAdminUser

from ..models import MediaFile
from .serializers import MediaFileSerializer


class MediaFileViewSet(viewsets.ModelViewSet):
    """Admin-only media library. Not public -- product images are served via
    their own product-scoped endpoints; this is for general assets."""

    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["folder"]
    search_fields = ["original_name", "folder"]
    ordering_fields = ["created_at", "size"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
