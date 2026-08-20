"""Shared DRF serializer mixins.

TranslatedSerializerMixin is the ONLY place that resolves an object's
translated fields into the response -- concrete serializers just declare
which fields come from the translation row via `translated_fields`.
"""

from .i18n import get_translation, resolve_language


class TranslatedSerializerMixin:
    """Mix into a ModelSerializer for any model with a `translations`
    related manager (Category, Brand, Product, ...).

    Subclasses set `translated_fields`, e.g.:

        class ProductListSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
            translated_fields = ["name", "short_description"]

    The object's queryset MUST prefetch `translations` (or a filtered
    Prefetch of it) -- this mixin never issues its own query per object.
    """

    translated_fields: list[str] = []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        requested_language = resolve_language(request)
        resolved = get_translation(instance, requested_language)

        for field_name in self.translated_fields:
            value = getattr(resolved.translation, field_name, "") if resolved.translation else ""
            data[field_name] = value

        data["language"] = resolved.language
        data["translation_available"] = resolved.translation_available
        if not resolved.translation_available:
            data["requested_language"] = resolved.requested_language

        return data
