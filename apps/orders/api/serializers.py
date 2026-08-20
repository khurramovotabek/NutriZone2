from rest_framework import serializers

from apps.locations.api.serializers import CityMiniSerializer, CountryMiniSerializer, RegionMiniSerializer
from apps.locations.models import City, Country, Region

from ..models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "variant", "product_name", "variant_name", "sku", "price", "quantity", "subtotal"]
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "full_name",
            "phone_number",
            "status",
            "total_price",
            "total_quantity",
            "created_at",
        ]
        read_only_fields = fields


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)
    country_detail = CountryMiniSerializer(source="country", read_only=True)
    region_detail = RegionMiniSerializer(source="region", read_only=True)
    city_detail = CityMiniSerializer(source="city", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "full_name",
            "phone_number",
            "telegram_username",
            "country",
            "country_detail",
            "region",
            "region_detail",
            "city",
            "city_detail",
            "delivery_address",
            "comment",
            "status",
            "items",
            "total_price",
            "total_quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    """Checkout payload. Cart is resolved server-side via X-Cart-Id / auth,
    not passed in the body, so totals can never be spoofed by the client."""

    full_name = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=20)
    telegram_username = serializers.CharField(max_length=64, required=False, allow_blank=True)

    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.filter(is_active=True))
    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.filter(is_active=True))
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.filter(is_active=True))
    delivery_address = serializers.CharField()

    comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        region = attrs.get("region")
        if region and region.country_id != attrs["country"].id:
            raise serializers.ValidationError(
                {"region": "Selected region does not belong to the selected country."}
            )
        city = attrs.get("city")
        if city and region and city.region_id != region.id:
            raise serializers.ValidationError(
                {"city": "Selected city does not belong to the selected region."}
            )
        return attrs


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
