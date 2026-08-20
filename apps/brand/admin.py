from django.contrib import admin

from apps.shared.constants import LANGUAGES

from .models import Brand, BrandTranslation


class BrandTranslationInline(admin.TabularInline):
    model = BrandTranslation
    fields = ["language", "description"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj is None:
            return len(LANGUAGES)
        return max(0, len(LANGUAGES) - obj.translations.count())

    def get_max_num(self, request, obj=None, **kwargs):
        return len(LANGUAGES)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "country", "website", "is_active", "created_at"]
    list_editable = ["is_active"]
    list_filter = ["is_active", "country"]
    search_fields = ["name", "translations__description"]
    autocomplete_fields = ["country"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BrandTranslationInline]
