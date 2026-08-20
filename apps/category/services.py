from django.db import transaction

from apps.shared.exceptions import ServiceError
from apps.shared.i18n import get_translation

from .models import Category, CategoryTranslation


class CategoryService:
    @staticmethod
    def validate_unique_translation(
        name: str, category: Category, language: str, instance: CategoryTranslation | None = None
    ) -> None:
        """Two checks, both scoped to `language`:
        1. This category doesn't already have a translation in this
           language (that's an update, not a create -- caught here so it's
           a clean 400 instead of the DB's raw IntegrityError).
        2. No SIBLING category has the same name in this language.
        """
        same_category_qs = CategoryTranslation.objects.filter(category=category, language=language)
        if instance:
            same_category_qs = same_category_qs.exclude(pk=instance.pk)
        if same_category_qs.exists():
            raise ServiceError(
                "This category already has a translation for this language.", code="duplicate_translation"
            )

        sibling_qs = CategoryTranslation.objects.filter(
            language=language, category__parent=category.parent, name__iexact=name
        ).exclude(category=category)
        if sibling_qs.exists():
            raise ServiceError(
                "A category with this name already exists at this level.", code="duplicate_category"
            )

    @staticmethod
    def get_breadcrumbs(category: Category) -> list[Category]:
        """Ancestors only (root-to-parent), NOT including `category` itself
        -- the path's last segment is always self by construction. Callers
        that want the full displayed trail append the category itself."""
        segment_ids = [pk for pk in category.path.strip("/").split("/") if pk]
        ancestor_ids = segment_ids[:-1]
        ancestors_by_id = {
            str(c.id): c
            for c in Category.objects.filter(id__in=ancestor_ids).prefetch_related("translations")
        }
        return [ancestors_by_id[pk] for pk in ancestor_ids if pk in ancestors_by_id]

    @staticmethod
    def descendant_ids(category: Category, include_self: bool = True) -> list[str]:
        """All descendant category ids via an indexed path prefix match --
        no recursive SQL needed."""
        qs = Category.objects.filter(path__startswith=category.path).values_list("id", flat=True)
        ids = [str(pk) for pk in qs]
        if not include_self:
            ids = [pk for pk in ids if pk != str(category.id)]
        return ids

    @staticmethod
    @transaction.atomic
    def reparent(category: Category, new_parent: Category | None) -> Category:
        """Move a category (and all its descendants) under a new parent,
        recomputing path/depth for the whole moved subtree in one pass.

        Deliberately does NOT check translation-name collisions against the
        new siblings -- reparenting is a structural move, not a rename;
        name-collision checking happens when a translation is actually
        written (CategoryService.validate_unique_translation), not here.
        """
        if new_parent and new_parent.id == category.id:
            raise ServiceError("A category cannot be its own parent.", code="invalid_parent")
        if new_parent and new_parent.path.startswith(category.path):
            raise ServiceError(
                "Cannot move a category under one of its own descendants.", code="circular_parent"
            )

        old_path = category.path
        descendants = list(Category.objects.filter(path__startswith=old_path).exclude(pk=category.pk))

        category.parent = new_parent
        category.save()  # recomputes category.path/depth via Category.save()

        depth_delta = category.depth - (len(old_path.strip("/").split("/")) - 1)
        for descendant in descendants:
            descendant.path = category.path + descendant.path[len(old_path) :]
            descendant.depth = descendant.depth + depth_delta
        Category.objects.bulk_update(descendants, ["path", "depth"])

        return category

    @staticmethod
    def build_tree(categories: list[Category], language: str) -> list[dict]:
        """Assemble a flat (already-ordered) category list into a nested
        tree of plain dicts, ready for the mega-menu endpoint. O(n), no
        extra queries -- the input list must already be prefetched
        (`translations`), since get_translation() never queries itself."""
        nodes: dict[str, dict] = {}
        for c in categories:
            resolved = get_translation(c, language)
            nodes[str(c.id)] = {
                "id": str(c.id),
                "name": resolved.translation.name if resolved.translation else c.slug,
                "slug": c.slug,
                "icon": c.icon,
                "image": c.image.url if c.image else None,
                "language": resolved.language,
                "children": [],
            }

        roots: list[dict] = []
        for category in categories:
            node = nodes[str(category.id)]
            parent_id = str(category.parent_id) if category.parent_id else None
            if parent_id and parent_id in nodes:
                nodes[parent_id]["children"].append(node)
            else:
                roots.append(node)
        return roots
