from rest_framework import serializers

from apps.orders.api.serializers import OrderListSerializer
from apps.products.models import ProductVariant
from apps.shared.i18n import get_translation, resolve_language


class LowStockVariantSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ["id", "sku", "product_name", "flavor", "weight", "quantity"]

    def get_product_name(self, obj):
        language = resolve_language(self.context.get("request"))
        resolved = get_translation(obj.product, language)
        return resolved.translation.name if resolved.translation else obj.product.slug


class OrdersByStatusSerializer(serializers.Serializer):
    new = serializers.IntegerField()
    pending = serializers.IntegerField()
    accepted = serializers.IntegerField()
    cancelled = serializers.IntegerField()


class DashboardOverviewSerializer(serializers.Serializer):
    generated_at = serializers.DateTimeField()
    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    total_variants = serializers.IntegerField()
    orders_by_status = OrdersByStatusSerializer()
    total_revenue = serializers.DecimalField(max_digits=16, decimal_places=2)
    out_of_stock_count = serializers.IntegerField()
    low_stock_variants = LowStockVariantSerializer(many=True)
    recent_orders = OrderListSerializer(many=True)
