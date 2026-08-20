from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ["variant", "quantity"]
    can_delete = False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "total_items", "subtotal", "updated_at"]
    search_fields = ["user__username", "id"]
    inlines = [CartItemInline]
    readonly_fields = ["user"]
