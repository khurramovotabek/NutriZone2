from rest_framework import serializers

from apps.brand.api.serializers import BrandMiniSerializer
from apps.category.api.serializers import CategoryMiniSerializer
from apps.shared.serializers import TranslatedSerializerMixin

from ..models import Product, ProductImage, ProductSpecification, ProductTranslation, ProductVariant
from ..selectors import product_catalog_base_queryset


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "is_primary", "sort_order", "alt_text"]
        read_only_fields = ["id"]


class ProductVariantSerializer(serializers.ModelSerializer):
    is_in_stock = serializers.BooleanField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "sku",
            "barcode",
            "price",
            "old_price",
            "quantity",
            "weight",
            "flavor",
            "is_default",
            "status",
            "is_in_stock",
            "discount_percent",
        ]
        read_only_fields = ["id"]

    def validate_sku(self, value):
        qs = ProductVariant.objects.filter(sku__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A variant with this SKU already exists.")
        return value

    def validate_barcode(self, value):
        if not value:
            return value
        qs = ProductVariant.objects.filter(barcode__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A variant with this barcode already exists.")
        return value

    def validate(self, attrs):
        price = attrs.get("price", getattr(self.instance, "price", None))
        old_price = attrs.get("old_price", getattr(self.instance, "old_price", None))
        if old_price is not None and price is not None and old_price < price:
            raise serializers.ValidationError(
                {"old_price": "Old price cannot be lower than the current price."}
            )
        return attrs


class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ["id", "label", "value", "sort_order"]
        read_only_fields = ["id"]


class ProductTranslationSerializer(serializers.ModelSerializer):
    """Manages a single (product, language) translation row -- nested
    under /products/{slug}/translations/, same pattern as
    images/variants/specifications."""

    class Meta:
        model = ProductTranslation
        fields = [
            "id",
            "language",
            "name",
            "short_description",
            "description",
            "meta_title",
            "meta_description",
        ]
        read_only_fields = ["id"]

    def validate_language(self, value):
        product = self.context.get("product")
        qs = ProductTranslation.objects.filter(product=product, language=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if product and qs.exists():
            raise serializers.ValidationError("This product already has a translation for this language.")
        return value


class ProductListSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Lean serializer for catalog/listing pages -- one cover image, price range.

    `name`/`short_description` are injected by TranslatedSerializerMixin.
    """

    translated_fields = ["name", "short_description"]

    category = CategoryMiniSerializer(read_only=True)
    brand = BrandMiniSerializer(read_only=True)
    cover_image = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()
    rating_average = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "category",
            "brand",
            "cover_image",
            "min_price",
            "is_in_stock",
            "rating_average",
            "rating_count",
            "is_active",
            "created_at",
        ]

    def get_cover_image(self, obj):
        images = list(obj.images.all())
        if not images:
            return None
        primary = next((i for i in images if i.is_primary), images[0])
        request = self.context.get("request")
        url = primary.image.url
        return request.build_absolute_uri(url) if request else url

    def get_min_price(self, obj):
        return obj.min_price

    def get_is_in_stock(self, obj):
        return obj.is_in_stock

    def get_rating_average(self, obj):
        # Falls back to None when the queryset wasn't annotated (e.g. a
        # plain Product.objects.filter() built outside the selectors module).
        return getattr(obj, "rating_average", None)

    def get_rating_count(self, obj):
        return getattr(obj, "rating_count", 0)


class ProductDetailSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Full representation: images, variants, specifications, related products.

    Designed so the frontend needs exactly ONE request for a product page.
    `name`/`short_description`/`description`/`meta_title`/`meta_description`
    are injected by TranslatedSerializerMixin.
    """

    translated_fields = ["name", "short_description", "description", "meta_title", "meta_description"]

    category = CategoryMiniSerializer(read_only=True)
    brand = BrandMiniSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    related_products = serializers.SerializerMethodField()
    rating_average = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "category",
            "brand",
            "images",
            "variants",
            "specifications",
            "related_products",
            "rating_average",
            "rating_count",
            "is_active",
            "created_at",
        ]

    def get_rating_average(self, obj):
        return getattr(obj, "rating_average", None)

    def get_rating_count(self, obj):
        return getattr(obj, "rating_count", 0)

    def get_related_products(self, obj):
        related = (
            product_catalog_base_queryset()
            .filter(category=obj.category, is_active=True)
            .exclude(pk=obj.pk)[:8]
        )
        return ProductListSerializer(related, many=True, context=self.context).data


class ProductWriteSerializer(serializers.ModelSerializer):
    """Used for admin create/update of the core product record.

    Translations, images/variants/specifications are managed via their own
    nested endpoints, keeping this serializer simple and avoiding fragile
    deep-nested writes. `slug` is required and manually set -- there's no
    `name` on this model to auto-derive it from anymore.
    """

    class Meta:
        model = Product
        fields = ["id", "category", "brand", "slug", "is_active"]
        read_only_fields = ["id"]

    def to_representation(self, instance):
        return ProductDetailSerializer(instance, context=self.context).data
