import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("category", "0003_backfill_path_depth"),
    ]

    operations = [
        migrations.CreateModel(
            name="CategoryTranslation",
            fields=[
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "language",
                    models.CharField(
                        choices=[("uz", "Uzbek"), ("ru", "Russian"), ("en", "English")], max_length=5
                    ),
                ),
                ("name", models.CharField(max_length=150)),
                ("description", models.TextField(blank=True)),
                ("meta_title", models.CharField(blank=True, max_length=255)),
                ("meta_description", models.CharField(blank=True, max_length=500)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="category.category",
                    ),
                ),
            ],
            options={
                "ordering": ["language"],
            },
        ),
        migrations.AddIndex(
            model_name="categorytranslation",
            index=models.Index(fields=["language"], name="category_ca_languag_76840d_idx"),
        ),
        migrations.AddIndex(
            model_name="categorytranslation",
            index=models.Index(fields=["category", "language"], name="category_ca_categor_04288c_idx"),
        ),
        migrations.AddConstraint(
            model_name="categorytranslation",
            constraint=models.UniqueConstraint(
                fields=("category", "language"), name="unique_category_translation"
            ),
        ),
    ]
