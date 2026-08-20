from django.contrib import admin
from django.utils.html import format_html

from apps.shared.constants import LANGUAGES

from .models import Category, CategoryTranslation

LANGUAGE_FLAGS = {"uz": "\U0001F1FA\U0001F1FF", "ru": "\U0001F1F7\U0001F1FA", "en": "\U0001F1EC\U0001F1E7"}


class CategoryTranslationInline(admin.TabularInline):
    model = CategoryTranslation
    extra = len(LANGUAGES)
    max_num = len(LANGUAGES)
    fields = ["language", "name", "description", "meta_title", "meta_description"]

    def get_extra(self, request, obj=None, **kwargs):
        # Only pad with blank rows up to 3 when creating fresh -- an
        # existing category with translations already filled shouldn't grow
        # extra blank rows every time an admin opens the page.
        if obj is None:
            return len(LANGUAGES)
        existing = obj.translations.count()
        return max(0, len(LANGUAGES) - existing)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["indented_display_name", "parent", "is_active", "sort_order", "created_at"]
    list_editable = ["is_active", "sort_order"]
    list_filter = ["is_active", "depth"]
    search_fields = ["slug", "translations__name"]
    autocomplete_fields = ["parent"]
    readonly_fields = ["path", "depth"]
    ordering = ["depth", "sort_order"]
    inlines = [CategoryTranslationInline]

    @admin.display(description="Name")
    def indented_display_name(self, obj):
        # Prefer English for the admin list view (store managers editing
        # translations are likely comfortable in en/ru); falls back to
        # whatever translation exists, then the slug.
        translation = obj.translations.filter(language="en").first() or obj.translations.first()
        label = translation.name if translation else obj.slug
        return format_html("&nbsp;&nbsp;&nbsp;&nbsp;" * obj.depth + "{}", label)


@admin.register(CategoryTranslation)
class CategoryTranslationAdmin(admin.ModelAdmin):
    list_display = ["category", "language_display", "name"]
    list_filter = ["language"]
    search_fields = ["name", "category__slug"]
    autocomplete_fields = ["category"]

    @admin.display(description="Language")
    def language_display(self, obj):
        return f"{LANGUAGE_FLAGS.get(obj.language, '')} {obj.get_language_display()}"
