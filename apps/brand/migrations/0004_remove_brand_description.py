from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("brand", "0003_backfill_brand_translations"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="brand",
            name="description",
        ),
    ]
