from django.db import transaction

from apps.cart.models import Cart
from apps.cart.services import CartService
from apps.products.services import VariantStockService
from apps.shared.constants import DEFAULT_LANGUAGE
from apps.shared.exceptions import ServiceError
from apps.shared.i18n import get_translation

from .models import Order, OrderItem

# Status transitions an admin/customer may perform, keyed by current status.
ALLOWED_TRANSITIONS = {
    Order.Status.NEW: {Order.Status.PENDING, Order.Status.CANCELLED},
    Order.Status.PENDING: {Order.Status.ACCEPTED, Order.Status.CANCELLED},
    Order.Status.ACCEPTED: set(),
    Order.Status.CANCELLED: set(),
}

# Statuses at which inventory has already been decremented for this order.
STOCK_DECREMENTED_STATUSES = {Order.Status.PENDING, Order.Status.ACCEPTED}


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_from_cart(
        cart: Cart, contact_data: dict, user=None, language: str = DEFAULT_LANGUAGE
    ) -> Order:
        """`language` is the customer's checkout-time language -- the
        OrderItem snapshot captures the product name in whatever language
        they were actually looking at, so their order history reads
        naturally later even if the catalog's translations change."""
        items = list(
            cart.items.select_related("variant", "variant__product").prefetch_related(
                "variant__product__translations"
            )
        )
        if not items:
            raise ServiceError("Your cart is empty.", code="empty_cart")

        # Re-validate availability at the moment of order creation. Stock is
        # NOT decremented yet -- only once an admin moves the order to
        # PENDING, per the marketplace's fulfillment workflow.
        for item in items:
            VariantStockService.assert_purchasable(item.variant, item.quantity)

        order = Order.objects.create(user=user, **contact_data)

        def _snapshot_name(item) -> str:
            resolved = get_translation(item.variant.product, language)
            return resolved.translation.name if resolved.translation else item.variant.product.slug

        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    variant=item.variant,
                    product_name=_snapshot_name(item),
                    variant_name=" / ".join(filter(None, [item.variant.flavor, item.variant.weight])),
                    sku=item.variant.sku,
                    price=item.variant.price,
                    quantity=item.quantity,
                )
                for item in items
            ]
        )
        CartService.clear(cart)
        return order

    @staticmethod
    @transaction.atomic
    def change_status(order: Order, new_status: str) -> Order:
        current = order.status
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        if new_status == current:
            return order
        if new_status not in allowed:
            raise ServiceError(
                f"Cannot change order status from '{current}' to '{new_status}'.",
                code="invalid_transition",
            )

        if new_status == Order.Status.PENDING:
            # This is the one moment stock actually leaves inventory.
            for item in order.items.select_related("variant"):
                if item.variant is None:
                    continue
                VariantStockService.decrease_stock(item.variant, item.quantity)

        if new_status == Order.Status.CANCELLED and current in STOCK_DECREMENTED_STATUSES:
            # Stock was already taken out for this order -- give it back.
            for item in order.items.select_related("variant"):
                if item.variant is None:
                    continue
                item.variant.quantity = item.variant.quantity + item.quantity
                item.variant.save(update_fields=["quantity", "updated_at"])

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        return order
