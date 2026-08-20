import django_filters

from apps.category.models import Category

from ..models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(method="filter_category")
    brand = django_filters.CharFilter(field_name="brand__slug")
    min_price = django_filters.NumberFilter(field_name="variants__price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="variants__price", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["category", "brand", "min_price", "max_price"]

    def filter_category(self, queryset, name, value):
        """Matching a category also matches every one of its descendants --
        landing on "Protein" should show Whey/Isolate/Casein products too,
        via the same indexed path-prefix lookup selectors.py uses."""
        try:
            category = Category.objects.only("path").get(slug=value)
        except Category.DoesNotExist:
            return queryset.none()
        return queryset.filter(category__path__startswith=category.path)
