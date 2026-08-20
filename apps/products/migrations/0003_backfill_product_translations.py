from django.db import migrations


def backfill_english_translations(apps, schema_editor):
    """Every product's existing (single-language, effectively English)
    content becomes its 'en' translation row -- admins add uz/ru afterward.
    Nothing is deleted here; the old columns are removed in a later
    migration, after this one has safely copied their contents forward."""
    Product = apps.get_model("products", "Product")
    ProductTranslation = apps.get_model("products", "ProductTranslation")

    ProductTranslation.objects.bulk_create(
        [
            ProductTranslation(
                product=product,
                language="en",
                name=product.name,
                short_description=product.short_description,
                description=product.description,
                meta_title=product.meta_title,
                meta_description=product.meta_description,
            )
            for product in Product.objects.all()
        ]
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0002_create_product_translation"),
    ]

    operations = [
        migrations.RunPython(backfill_english_translations, noop_reverse),
    ]
