from django.urls import path

from .views import (
    CartDetailView,
    CartItemDecreaseView,
    CartItemDetailView,
    CartItemIncreaseView,
    CartItemListView,
)

app_name = "cart"

urlpatterns = [
    path("", CartDetailView.as_view(), name="cart-detail"),
    path("items/", CartItemListView.as_view(), name="cart-item-list"),
    path("items/<uuid:item_id>/", CartItemDetailView.as_view(), name="cart-item-detail"),
    path("items/<uuid:item_id>/increase/", CartItemIncreaseView.as_view(), name="cart-item-increase"),
    path("items/<uuid:item_id>/decrease/", CartItemDecreaseView.as_view(), name="cart-item-decrease"),
]
