from rest_framework import serializers

from apps.locations.api.serializers import CountryMiniSerializer
from apps.shared.serializers import TranslatedSerializerMixin

from ..models import Brand, BrandTranslation


class BrandSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """`description` is injected by TranslatedSerializerMixin from the
    prefetched `translations` relation -- manage it via
    /brands/{slug}/translations/ (see BrandTranslationListCreateView)."""

    translated_fields = ["description"]

    product_count = serializers.IntegerField(read_only=True, default=0)
    country_detail = CountryMiniSerializer(source="country", read_only=True)

    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "website",
            "country",
            "country_detail",
            "is_active",
            "product_count",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]


class BrandMiniSerializer(serializers.ModelSerializer):
    country_detail = CountryMiniSerializer(source="country", read_only=True)

    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "logo", "country_detail"]


class BrandTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandTranslation
        fields = ["id", "language", "description"]
        read_only_fields = ["id"]

    def validate_language(self, value):
        brand = self.context.get("brand")
        qs = BrandTranslation.objects.filter(brand=brand, language=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if brand and qs.exists():
            raise serializers.ValidationError("This brand already has a translation for this language.")
        return value
