from django.db import migrations


def backfill_english_translations(apps, schema_editor):
    """Every brand's existing (single-language, effectively English) content
    becomes its 'en' translation row -- admins add uz/ru afterward through
    the normal translation-management UI. Nothing is deleted here; the old
    `description` column is removed in a separate, later migration."""
    Brand = apps.get_model("brand", "Brand")
    BrandTranslation = apps.get_model("brand", "BrandTranslation")

    BrandTranslation.objects.bulk_create(
        [BrandTranslation(brand=brand, language="en", description=brand.description) for brand in Brand.objects.all()]
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("brand", "0002_create_brand_translation"),
    ]

    operations = [
        migrations.RunPython(backfill_english_translations, noop_reverse),
    ]
