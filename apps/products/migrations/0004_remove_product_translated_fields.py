from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_backfill_product_translations"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="description",
        ),
        migrations.RemoveField(
            model_name="product",
            name="meta_description",
        ),
        migrations.RemoveField(
            model_name="product",
            name="meta_title",
        ),
        migrations.RemoveField(
            model_name="product",
            name="name",
        ),
        migrations.RemoveField(
            model_name="product",
            name="short_description",
        ),
        migrations.AlterField(
            model_name="product",
            name="slug",
            field=models.SlugField(max_length=280, unique=True),
        ),
    ]
