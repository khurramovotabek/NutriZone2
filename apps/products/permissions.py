"""Permission classes for the products domain.

The catalog only needs the generic admin-or-read-only rule, so it's
imported directly from apps.shared rather than duplicated here. This file
exists so the app follows the standard structure and is the natural place
to add product-specific permissions later (e.g. "vendor can only edit their
own products" once multi-vendor support exists).
"""

from apps.shared.permissions import IsAdminOrReadOnly

__all__ = ["IsAdminOrReadOnly"]
