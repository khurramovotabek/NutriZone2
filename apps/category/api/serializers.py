from rest_framework import serializers

from apps.shared.exceptions import ServiceError
from apps.shared.serializers import TranslatedSerializerMixin

from ..models import Category, CategoryTranslation
from ..services import CategoryService


class CategorySerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Translated fields (name, description, meta_title, meta_description)
    are injected by TranslatedSerializerMixin from the prefetched
    `translations` relation -- they're intentionally not declared here, so
    writing them through this serializer isn't possible. Manage them via
    /categories/{slug}/translations/ instead (see CategoryTranslationView)."""

    translated_fields = ["name", "description", "meta_title", "meta_description"]

    product_count = serializers.IntegerField(read_only=True, default=0)
    depth = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "parent",
            "slug",
            "icon",
            "image",
            "is_active",
            "sort_order",
            "depth",
            "product_count",
            "created_at",
        ]
        read_only_fields = ["id", "depth", "created_at"]

    def validate(self, attrs):
        if self.instance and "parent" in attrs and attrs["parent"] != self.instance.parent:
            raise serializers.ValidationError(
                {"parent": "Changing parent here would not update descendants' paths. Use the move action."}
            )
        return attrs


class CategoryMiniSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Lightweight representation embedded in product responses."""

    translated_fields = ["name"]

    class Meta:
        model = Category
        fields = ["id", "slug", "icon", "image"]


class CategoryMoveSerializer(serializers.Serializer):
    """Payload for the admin-only reparent action."""

    parent = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), allow_null=True)


class CategoryTranslationSerializer(serializers.ModelSerializer):
    """Manages a single (category, language) translation row -- nested
    under /categories/{slug}/translations/, the same pattern used for
    ProductImage/Variant/Specification."""

    class Meta:
        model = CategoryTranslation
        fields = ["id", "language", "name", "description", "meta_title", "meta_description"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        category = self.context["category"]
        language = attrs.get("language", getattr(self.instance, "language", None))
        name = attrs.get("name", getattr(self.instance, "name", None))
        try:
            CategoryService.validate_unique_translation(name, category, language, instance=self.instance)
        except ServiceError as exc:
            raise serializers.ValidationError(exc.message) from exc
        return attrs
