from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("category", "0005_backfill_category_translations"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="category",
            options={"ordering": ["sort_order"], "verbose_name_plural": "Categories"},
        ),
        migrations.RemoveConstraint(
            model_name="category",
            name="unique_category_name_per_parent",
        ),
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(max_length=170, unique=True),
        ),
        migrations.RemoveField(
            model_name="category",
            name="description",
        ),
        migrations.RemoveField(
            model_name="category",
            name="meta_description",
        ),
        migrations.RemoveField(
            model_name="category",
            name="meta_title",
        ),
        migrations.RemoveField(
            model_name="category",
            name="name",
        ),
    ]
