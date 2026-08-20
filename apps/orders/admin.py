from django.contrib import admin, messages

from apps.shared.exceptions import ServiceError

from .models import Order, OrderItem
from .services import OrderService


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["variant", "product_name", "variant_name", "sku", "price", "quantity", "subtotal"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "full_name",
        "phone_number",
        "city",
        "status",
        "total_price",
        "created_at",
    ]
    list_filter = ["status", "country", "created_at"]
    search_fields = ["order_number", "full_name", "phone_number", "telegram_username"]
    readonly_fields = ["order_number", "user", "total_price", "total_quantity", "created_at", "updated_at"]
    autocomplete_fields = ["country", "region", "city"]
    inlines = [OrderItemInline]
    actions = ["mark_pending", "mark_accepted", "mark_cancelled"]

    def _bulk_transition(self, request, queryset, new_status):
        succeeded, failed = 0, 0
        for order in queryset:
            try:
                OrderService.change_status(order, new_status)
                succeeded += 1
            except ServiceError:
                failed += 1
        if succeeded:
            self.message_user(request, f"{succeeded} order(s) moved to {new_status}.", level=messages.SUCCESS)
        if failed:
            self.message_user(
                request, f"{failed} order(s) could not transition to {new_status}.", level=messages.WARNING
            )

    @admin.action(description="Mark selected orders as PENDING (decreases stock)")
    def mark_pending(self, request, queryset):
        self._bulk_transition(request, queryset, Order.Status.PENDING)

    @admin.action(description="Mark selected orders as ACCEPTED")
    def mark_accepted(self, request, queryset):
        self._bulk_transition(request, queryset, Order.Status.ACCEPTED)

    @admin.action(description="Cancel selected orders (restocks if needed)")
    def mark_cancelled(self, request, queryset):
        self._bulk_transition(request, queryset, Order.Status.CANCELLED)
