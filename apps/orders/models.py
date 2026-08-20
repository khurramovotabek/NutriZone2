from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.locations.models import City, Country, Region
from apps.products.models import ProductVariant
from apps.shared.models import BaseModel


class Order(BaseModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )

    # Contact/delivery snapshot -- collected at checkout regardless of login
    # state, since there is no online payment step to tie the order to an
    # account. This is what admins use to actually fulfill the order.
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    telegram_username = models.CharField(max_length=64, blank=True)

    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    region = models.ForeignKey(
        Region, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    delivery_address = models.TextField(help_text="Street, building, apartment, landmark, etc.")

    comment = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)

    order_number = models.CharField(max_length=20, unique=True, editable=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    def _generate_order_number(self):
        from django.utils.crypto import get_random_string

        return f"NZ-{get_random_string(8).upper()}"

    @property
    def full_delivery_location(self):
        """Human-readable 'City, Region, Country' string for admin/display."""
        parts = [
            self.city.name if self.city else None,
            self.region.name if self.region else None,
            self.country.name if self.country else None,
        ]
        return ", ".join(p for p in parts if p)

    @property
    def total_price(self):
        return sum((item.subtotal for item in self.items.all()), start=Decimal("0.00"))

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(BaseModel):
    """Immutable snapshot of a purchased line item.

    Deliberately does NOT foreign-key into live pricing -- product_name,
    variant_name and price are copied at order-creation time so historical
    orders never change even if the catalog does later.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, related_name="order_items"
    )

    product_name = models.CharField(max_length=255)
    variant_name = models.CharField(max_length=255, blank=True)
    sku = models.CharField(max_length=100)

    price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.quantity} x {self.product_name} ({self.variant_name})"

    @property
    def subtotal(self):
        return self.price * self.quantity
