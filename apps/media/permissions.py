"""Permission classes for the media domain -- uses the shared admin-only rule."""

from apps.shared.permissions import IsAdminUser

__all__ = ["IsAdminUser"]
