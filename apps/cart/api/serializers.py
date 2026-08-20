from rest_framework import serializers

from apps.products.models import ProductVariant
from apps.shared.i18n import get_translation, resolve_language

from ..models import Cart, CartItem


class CartItemVariantSerializer(serializers.ModelSerializer):
    """Minimal variant snapshot embedded inside cart item responses."""

    product_name = serializers.SerializerMethodField()
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "sku",
            "product_name",
            "product_slug",
            "cover_image",
            "price",
            "old_price",
            "weight",
            "flavor",
            "quantity",
            "status",
        ]

    def get_product_name(self, obj):
        language = resolve_language(self.context.get("request"))
        resolved = get_translation(obj.product, language)
        return resolved.translation.name if resolved.translation else obj.product.slug

    def get_cover_image(self, obj):
        image = obj.product.images.filter(is_primary=True).first() or obj.product.images.first()
        if not image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(image.image.url) if request else image.image.url


class CartItemSerializer(serializers.ModelSerializer):
    variant_detail = CartItemVariantSerializer(source="variant", read_only=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "variant", "variant_detail", "quantity", "subtotal"]
        extra_kwargs = {"variant": {"write_only": True}}


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "items", "total_items", "total_quantity", "subtotal", "total_price", "updated_at"]


class AddCartItemSerializer(serializers.Serializer):
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
