import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductTranslation",
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
                ("name", models.CharField(max_length=255)),
                ("short_description", models.CharField(blank=True, max_length=500)),
                ("description", models.TextField(blank=True)),
                ("meta_title", models.CharField(blank=True, max_length=255)),
                ("meta_description", models.CharField(blank=True, max_length=500)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="products.product",
                    ),
                ),
            ],
            options={
                "ordering": ["language"],
                "indexes": [
                    models.Index(fields=["language"], name="products_pr_languag_a03b26_idx"),
                    models.Index(fields=["product", "language"], name="products_pr_product_fbbaf9_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("product", "language"), name="unique_product_translation")
                ],
            },
        ),
    ]
