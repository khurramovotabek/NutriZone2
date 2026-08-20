from django.db import migrations


def backfill_path_and_depth(apps, schema_editor):
    """Any category that existed before the tree fields were added has
    parent=NULL (the FK defaulted to null) and path='' (CharField's
    implicit blank default). Since they had no parent concept before,
    they're all roots -- path becomes their own id, depth 0. Categories
    created after this migration go through Category.save(), which
    computes this correctly on its own.
    """
    Category = apps.get_model("category", "Category")
    categories = list(Category.objects.filter(path=""))
    for category in categories:
        category.path = f"{category.id}/"
        category.depth = 0
    if categories:
        Category.objects.bulk_update(categories, ["path", "depth"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("category", "0002_category_depth_category_icon_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_path_and_depth, noop_reverse),
    ]
