from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.products.models import ProductVariant
from apps.shared.models import BaseModel


class Cart(BaseModel):
    """A shopping cart.

    Either owned by an authenticated user, or anonymous and identified by
    its own UUID (the frontend stores this id, e.g. in a cookie, and sends
    it back on subsequent requests via the X-Cart-Id header).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="cart"
    )

    def __str__(self):
        return f"Cart {self.id} ({'user: ' + str(self.user) if self.user_id else 'guest'})"

    @property
    def total_items(self):
        return self.items.count()

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum((item.subtotal for item in self.items.all()), start=0)

    @property
    def total_price(self):
        # No taxes/shipping/discounts yet -- kept separate from subtotal so
        # future modules (coupons, delivery fees) can hook in without
        # touching the cart's core calculation.
        return self.subtotal


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["cart", "variant"], name="unique_cart_variant")]

    def __str__(self):
        return f"{self.quantity} x {self.variant}"

    @property
    def unit_price(self):
        return self.variant.price

    @property
    def subtotal(self):
        return self.variant.price * self.quantity
