from django.db.models import Count
from django.utils import timezone

from apps.orders.models import Order
from apps.products.models import Product, ProductVariant

LOW_STOCK_THRESHOLD = 5


class DashboardService:
    @staticmethod
    def get_overview() -> dict:
        orders_by_status = dict(Order.objects.values_list("status").annotate(count=Count("id")))

        accepted_orders = Order.objects.filter(status=Order.Status.ACCEPTED).prefetch_related("items")
        total_revenue = sum((order.total_price for order in accepted_orders), start=0)

        low_stock_variants = (
            ProductVariant.objects.filter(
                status=ProductVariant.Status.ACTIVE, quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0
            )
            .select_related("product")
            .prefetch_related("product__translations")
            .order_by("quantity")[:20]
        )
        out_of_stock_count = ProductVariant.objects.filter(
            status=ProductVariant.Status.ACTIVE, quantity=0
        ).count()

        recent_orders = Order.objects.order_by("-created_at")[:10]

        return {
            "generated_at": timezone.now(),
            "total_products": Product.objects.count(),
            "active_products": Product.objects.filter(is_active=True).count(),
            "total_variants": ProductVariant.objects.count(),
            "orders_by_status": {
                "new": orders_by_status.get(Order.Status.NEW, 0),
                "pending": orders_by_status.get(Order.Status.PENDING, 0),
                "accepted": orders_by_status.get(Order.Status.ACCEPTED, 0),
                "cancelled": orders_by_status.get(Order.Status.CANCELLED, 0),
            },
            "total_revenue": total_revenue,
            "out_of_stock_count": out_of_stock_count,
            "low_stock_variants": low_stock_variants,
            "recent_orders": recent_orders,
        }
