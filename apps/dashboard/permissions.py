"""Permission classes for the dashboard domain -- admin-only."""

from apps.shared.permissions import IsAdminUser

__all__ = ["IsAdminUser"]
