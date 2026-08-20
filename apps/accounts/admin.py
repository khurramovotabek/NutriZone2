from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_joined"]
    list_display = [
        "username",
        "email",
        "phone_number",
        "is_customer",
        "is_staff",
        "is_active",
        "date_joined",
    ]
    list_filter = ["is_staff", "is_customer", "is_active"]
    search_fields = ["username", "email", "phone_number", "first_name", "last_name"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Marketplace Info", {"fields": ("phone_number", "telegram_username", "is_customer")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Marketplace Info", {"fields": ("phone_number", "telegram_username", "is_customer")}),
    )
