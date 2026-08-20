from django.db import migrations


def backfill_english_translations(apps, schema_editor):
    """Every category's existing (single-language, effectively English)
    content becomes its 'en' translation row -- admins add uz/ru afterward.
    Nothing is deleted here; the old columns are removed in a later
    migration, after this one has safely copied their contents forward."""
    Category = apps.get_model("category", "Category")
    CategoryTranslation = apps.get_model("category", "CategoryTranslation")

    CategoryTranslation.objects.bulk_create(
        [
            CategoryTranslation(
                category=category,
                language="en",
                name=category.name,
                description=category.description,
                meta_title=category.meta_title,
                meta_description=category.meta_description,
            )
            for category in Category.objects.all()
        ]
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("category", "0004_create_category_translation"),
    ]

    operations = [
        migrations.RunPython(backfill_english_translations, noop_reverse),
    ]
