"""Permission classes for the locations domain -- uses the shared generic rule."""

from apps.shared.permissions import IsAdminOrReadOnly

__all__ = ["IsAdminOrReadOnly"]
