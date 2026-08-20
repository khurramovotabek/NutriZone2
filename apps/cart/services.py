from django.db import transaction

from apps.products.models import ProductVariant
from apps.shared.exceptions import ServiceError

from .models import Cart, CartItem


class CartService:
    @staticmethod
    def get_or_create_cart(*, user=None, cart_id=None) -> Cart:
        """Resolve the active cart for this request.

        Authenticated users always get their own persistent cart. Guests are
        identified by a cart_id the frontend stores and replays.
        """
        if user and user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=user)
            return cart
        if cart_id:
            cart, _ = Cart.objects.get_or_create(id=cart_id)
            return cart
        return Cart.objects.create()

    @staticmethod
    @transaction.atomic
    def add_item(cart: Cart, variant: ProductVariant, quantity: int) -> CartItem:
        if variant.status != ProductVariant.Status.ACTIVE:
            raise ServiceError(f"'{variant}' is not currently available.", code="variant_inactive")

        item, created = CartItem.objects.select_for_update().get_or_create(
            cart=cart, variant=variant, defaults={"quantity": 0}
        )
        new_quantity = item.quantity + quantity
        if new_quantity > variant.quantity:
            raise ServiceError(
                f"Only {variant.quantity} unit(s) of '{variant}' are available.", code="insufficient_stock"
            )
        item.quantity = new_quantity
        item.save(update_fields=["quantity", "updated_at"])
        return item

    @staticmethod
    def set_quantity(cart: Cart, item: CartItem, quantity: int) -> CartItem:
        if quantity > item.variant.quantity:
            raise ServiceError(
                f"Only {item.variant.quantity} unit(s) of '{item.variant}' are available.",
                code="insufficient_stock",
            )
        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        return item

    @staticmethod
    def increase_quantity(cart: Cart, item: CartItem, step: int = 1) -> CartItem:
        return CartService.set_quantity(cart, item, item.quantity + step)

    @staticmethod
    def decrease_quantity(cart: Cart, item: CartItem, step: int = 1) -> CartItem | None:
        new_quantity = item.quantity - step
        if new_quantity <= 0:
            item.delete()
            return None
        item.quantity = new_quantity
        item.save(update_fields=["quantity", "updated_at"])
        return item

    @staticmethod
    def remove_item(cart: Cart, item: CartItem) -> None:
        item.delete()

    @staticmethod
    def clear(cart: Cart) -> None:
        cart.items.all().delete()
