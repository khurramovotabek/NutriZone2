"""
API v1 route aggregation.

Keeping this in its own module (rather than inlining everything in
config/urls.py) means a future v2 can be added as a sibling file without
touching v1's wiring or any individual app.
"""

from django.urls import include, path

from apps.reviews.api.urls import product_review_urlpatterns

urlpatterns = [
    # Auth & profile
    path("auth/", include("apps.accounts.api.urls")),
    # Catalog
    path("categories/", include("apps.category.api.urls")),
    path("brands/", include("apps.brand.api.urls")),
    path("products/", include("apps.products.api.urls")),
    path("products/", include(product_review_urlpatterns)),
    path("locations/", include("apps.locations.api.urls")),
    # Reviews (flat detail endpoint -- /reviews/{id}/)
    path("reviews/", include("apps.reviews.api.urls")),
    # Notifications
    path("notifications/", include("apps.notifications.api.urls")),
    # Shopping
    path("cart/", include("apps.cart.api.urls")),
    path("orders/", include("apps.orders.api.urls")),
    # Admin-facing
    path("media/", include("apps.media.api.urls")),
    path("dashboard/", include("apps.dashboard.api.urls")),
    path("settings/", include("apps.site_settings.api.urls")),
]
