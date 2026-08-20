"""Test-only factory helpers.

Category/Product no longer have a bare `name` field (see the i18n
architecture) -- every test that used to do
`Product.objects.create(name="Whey Protein", ...)` needs to create the base
row plus a translation row instead. These two helpers do that in one call
so it isn't reimplemented per test file.
"""

from django.utils.text import slugify

from apps.category.models import Category, CategoryTranslation
from apps.products.models import Product, ProductTranslation


def make_category(
    name: str, *, parent=None, language: str = "en", slug: str | None = None, **kwargs
) -> Category:
    category = Category.objects.create(parent=parent, slug=slug or slugify(name), **kwargs)
    CategoryTranslation.objects.create(category=category, language=language, name=name)
    return category


def make_product(
    name: str, *, category, brand, language: str = "en", slug: str | None = None, **kwargs
) -> Product:
    product = Product.objects.create(category=category, brand=brand, slug=slug or slugify(name), **kwargs)
    ProductTranslation.objects.create(product=product, language=language, name=name)
    return product
