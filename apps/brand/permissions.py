"""Permission classes for the brand domain -- uses the shared generic rule."""

from apps.shared.permissions import IsAdminOrReadOnly

__all__ = ["IsAdminOrReadOnly"]
