"""Permission classes for the notifications domain.

Ownership is enforced via the queryset (notifications_for_user), not a
separate permission class -- there's no scenario where a user needs
object-level access to someone else's notification.
"""
