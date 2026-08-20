import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("brand", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BrandTranslation",
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
                ("description", models.TextField(blank=True)),
                (
                    "brand",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="brand.brand",
                    ),
                ),
            ],
            options={
                "ordering": ["language"],
                "indexes": [
                    models.Index(fields=["language"], name="brand_brand_languag_863543_idx"),
                    models.Index(fields=["brand", "language"], name="brand_brand_brand_i_89e090_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("brand", "language"), name="unique_brand_translation")
                ],
            },
        ),
    ]
