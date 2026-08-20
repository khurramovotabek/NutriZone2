"""Permission classes for the orders domain -- uses the shared admin rule.

Ownership filtering (a customer only sees their own orders) is handled in
selectors.orders_visible_to_user rather than as an object-level permission,
since it needs to change *which rows* are queryable, not just gate access to
a single already-fetched object.
"""

from apps.shared.permissions import IsAdminUser

__all__ = ["IsAdminUser"]
