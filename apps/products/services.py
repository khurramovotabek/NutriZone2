from django.db.models import Q, QuerySet

from apps.shared.exceptions import ServiceError

from .models import ProductVariant


class ProductService:
    @staticmethod
    def search(queryset: QuerySet, query: str) -> QuerySet:
        """Search across product name/description (any language), brand,
        category name (any language), SKU, barcode. Deliberately searches
        all languages' translations rather than just the request's current
        language -- a Russian-speaking user typing part of an English brand
        name should still find it."""
        if not query:
            return queryset
        return queryset.filter(
            Q(translations__name__icontains=query)
            | Q(translations__description__icontains=query)
            | Q(translations__short_description__icontains=query)
            | Q(brand__name__icontains=query)
            | Q(category__translations__name__icontains=query)
            | Q(variants__sku__icontains=query)
            | Q(variants__barcode__icontains=query)
        ).distinct()

    @staticmethod
    def filter_by_availability(queryset: QuerySet, availability: str) -> QuerySet:
        if availability == "in_stock":
            return queryset.filter(
                variants__status=ProductVariant.Status.ACTIVE, variants__quantity__gt=0
            ).distinct()
        if availability == "out_of_stock":
            return queryset.exclude(
                variants__status=ProductVariant.Status.ACTIVE, variants__quantity__gt=0
            ).distinct()
        return queryset


class VariantStockService:
    @staticmethod
    def assert_purchasable(variant: ProductVariant, requested_quantity: int) -> None:
        if variant.status != ProductVariant.Status.ACTIVE:
            raise ServiceError(f"'{variant}' is not currently available.", code="variant_inactive")
        if variant.quantity < requested_quantity:
            raise ServiceError(
                f"Only {variant.quantity} unit(s) of '{variant}' are in stock.",
                code="insufficient_stock",
            )

    @staticmethod
    def decrease_stock(variant: ProductVariant, quantity: int) -> None:
        updated = ProductVariant.objects.filter(pk=variant.pk, quantity__gte=quantity).update(
            quantity=variant.quantity - quantity
        )
        if not updated:
            raise ServiceError(f"Insufficient stock for '{variant}'.", code="insufficient_stock")
