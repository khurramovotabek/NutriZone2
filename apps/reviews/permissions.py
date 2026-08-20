"""Permission classes for the reviews domain -- uses the shared generic rules."""

from apps.shared.permissions import IsOwnerOrAdmin

__all__ = ["IsOwnerOrAdmin"]
