from django.contrib import admin

from apps.shared.constants import LANGUAGES

from .models import Product, ProductImage, ProductSpecification, ProductTranslation, ProductVariant


class ProductTranslationInline(admin.TabularInline):
    model = ProductTranslation
    fields = ["language", "name", "short_description", "description", "meta_title", "meta_description"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj is None:
            return len(LANGUAGES)
        return max(0, len(LANGUAGES) - obj.translations.count())

    def get_max_num(self, request, obj=None, **kwargs):
        return len(LANGUAGES)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "is_primary", "sort_order", "alt_text"]


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ["sku", "barcode", "price", "old_price", "quantity", "weight", "flavor", "is_default", "status"]


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1
    fields = ["label", "value", "sort_order"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["display_name", "slug", "category", "brand", "is_active", "created_at"]
    list_filter = ["is_active", "category", "brand"]
    list_editable = ["is_active"]
    search_fields = [
        "slug",
        "translations__name",
        "translations__description",
        "variants__sku",
        "variants__barcode",
    ]
    autocomplete_fields = ["category", "brand"]
    inlines = [ProductTranslationInline, ProductImageInline, ProductVariantInline, ProductSpecificationInline]

    @admin.display(description="Name")
    def display_name(self, obj):
        translation = obj.translations.filter(language="en").first() or obj.translations.first()
        return translation.name if translation else obj.slug


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["sku", "product", "price", "old_price", "quantity", "status", "is_default"]
    list_filter = ["status"]
    list_editable = ["price", "quantity", "status"]
    search_fields = ["sku", "barcode", "product__slug", "product__translations__name"]
    autocomplete_fields = ["product"]
