"""Permission classes for the category domain -- uses the shared generic rule."""

from apps.shared.permissions import IsAdminOrReadOnly

__all__ = ["IsAdminOrReadOnly"]
