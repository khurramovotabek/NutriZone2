from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.shared.exceptions import ServiceError
from apps.shared.test_helpers import make_category

from .models import Category, CategoryTranslation
from .services import CategoryService

User = get_user_model()


class CategoryTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")
        self.category = make_category("Protein", is_active=True)

    def test_list_categories_is_public(self):
        response = self.client.get(reverse("categories:category-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_requires_admin(self):
        response = self.client.post(reverse("categories:category-list"), {"slug": "creatine"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_create_category(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("categories:category-list"), {"slug": "creatine"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["slug"], "creatine")

    def test_list_shows_translated_name_falling_back_to_english(self):
        # No ?lang= given -> defaults to uz -> falls back to en since only
        # an English translation was created above.
        response = self.client.get(reverse("categories:category-list"))
        names = [c["name"] for c in response.data["results"]]
        self.assertIn("Protein", names)

    def test_inactive_category_hidden_from_public_list(self):
        make_category("Hidden", is_active=False)
        response = self.client.get(reverse("categories:category-list"))
        names = [c["name"] for c in response.data["results"]]
        self.assertNotIn("Hidden", names)


class CategoryTreeModelTests(APITestCase):
    """Model/service-level tests for the materialized path implementation."""

    def test_root_category_path(self):
        root = make_category("Sports Nutrition")
        self.assertEqual(root.depth, 0)
        self.assertEqual(root.path, f"{root.id}/")

    def test_child_path_includes_parent(self):
        root = make_category("Sports Nutrition")
        child = make_category("Protein", parent=root)
        self.assertEqual(child.depth, 1)
        self.assertEqual(child.path, f"{root.path}{child.id}/")

    def test_grandchild_path_and_depth(self):
        root = make_category("Sports Nutrition")
        protein = make_category("Protein", parent=root)
        whey = make_category("Whey Protein", parent=protein)
        self.assertEqual(whey.depth, 2)
        self.assertEqual(whey.path, f"{root.id}/{protein.id}/{whey.id}/")

    def test_same_name_allowed_under_different_parents(self):
        protein = make_category("Protein")
        vitamins = make_category("Vitamins")
        # "Minerals" under both -- should NOT raise. Distinct slugs since
        # slug is still globally unique; only the translated *name* is
        # allowed to repeat across different parents.
        make_category("Minerals", parent=protein, slug="minerals-protein")
        make_category("Minerals", parent=vitamins, slug="minerals-vitamins")
        self.assertEqual(CategoryTranslation.objects.filter(name="Minerals").count(), 2)

    def test_duplicate_name_same_parent_same_language_rejected(self):
        root = make_category("Sports Nutrition")
        make_category("Protein", parent=root, slug="protein")
        other = make_category("Creatine", parent=root, slug="creatine")
        with self.assertRaises(ServiceError):
            CategoryService.validate_unique_translation("protein", other, "en")

    def test_breadcrumbs(self):
        root = make_category("Sports Nutrition")
        protein = make_category("Protein", parent=root)
        whey = make_category("Whey Protein", parent=protein)
        breadcrumbs = CategoryService.get_breadcrumbs(whey)
        crumb_names = [c.translations.get(language="en").name for c in breadcrumbs]
        self.assertEqual(crumb_names, ["Sports Nutrition", "Protein"])

    def test_descendant_ids(self):
        root = make_category("Sports Nutrition")
        protein = make_category("Protein", parent=root)
        whey = make_category("Whey Protein", parent=protein)
        make_category("Vitamins")  # unrelated root

        descendants = CategoryService.descendant_ids(root)
        self.assertIn(str(protein.id), descendants)
        self.assertIn(str(whey.id), descendants)
        self.assertEqual(len(descendants), 3)  # root + protein + whey

    def test_reparent_cascades_descendant_paths(self):
        sports = make_category("Sports Nutrition")
        health = make_category("Health")
        protein = make_category("Protein", parent=sports)
        whey = make_category("Whey Protein", parent=protein)

        CategoryService.reparent(protein, health)
        protein.refresh_from_db()
        whey.refresh_from_db()

        self.assertEqual(protein.path, f"{health.path}{protein.id}/")
        self.assertEqual(protein.depth, 1)
        self.assertTrue(whey.path.startswith(protein.path))
        self.assertEqual(whey.depth, 2)

    def test_reparent_rejects_circular_move(self):
        root = make_category("Sports Nutrition")
        child = make_category("Protein", parent=root)
        with self.assertRaises(ServiceError):
            CategoryService.reparent(root, child)

    def test_build_tree_nests_correctly(self):
        root = make_category("Sports Nutrition")
        protein = make_category("Protein", parent=root)
        make_category("Whey Protein", parent=protein)
        make_category("Vitamins")

        categories = list(Category.objects.prefetch_related("translations").order_by("depth"))
        tree = CategoryService.build_tree(categories, "en")
        self.assertEqual(len(tree), 2)  # Sports Nutrition + Vitamins at root
        sports_node = next(n for n in tree if n["name"] == "Sports Nutrition")
        self.assertEqual(len(sports_node["children"]), 1)
        self.assertEqual(sports_node["children"][0]["children"][0]["name"], "Whey Protein")

    def test_build_tree_falls_back_when_language_missing(self):
        make_category("Sports Nutrition", language="en")
        categories = list(Category.objects.prefetch_related("translations"))
        tree = CategoryService.build_tree(categories, "ru")  # no ru translation exists
        self.assertEqual(tree[0]["name"], "Sports Nutrition")
        self.assertEqual(tree[0]["language"], "en")


class CategoryTreeApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")
        self.sports = make_category("Sports Nutrition")
        self.protein = make_category("Protein", parent=self.sports)
        self.whey = make_category("Whey Protein", parent=self.protein)

    def test_tree_endpoint(self):
        response = self.client.get(reverse("categories:category-tree"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {node["name"] for node in response.data}
        self.assertIn("Sports Nutrition", names)

    def test_breadcrumbs_endpoint(self):
        url = reverse("categories:category-breadcrumbs", kwargs={"slug": self.whey.slug})
        response = self.client.get(url)
        names = [c["name"] for c in response.data]
        self.assertEqual(names, ["Sports Nutrition", "Protein", "Whey Protein"])

    def test_move_requires_admin(self):
        url = reverse("categories:category-move", kwargs={"slug": self.protein.slug})
        response = self.client.post(url, {"parent": None}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_move_category(self):
        health = make_category("Health")
        self.client.force_authenticate(user=self.admin)
        url = reverse("categories:category-move", kwargs={"slug": self.protein.slug})
        response = self.client.post(url, {"parent": str(health.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.whey.refresh_from_db()
        self.assertTrue(self.whey.path.startswith(health.path))

    def test_ordinary_update_cannot_change_parent(self):
        health = make_category("Health")
        self.client.force_authenticate(user=self.admin)
        url = reverse("categories:category-detail", kwargs={"slug": self.protein.slug})
        response = self.client.patch(url, {"parent": str(health.id)})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CategoryTranslationApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")
        self.category = make_category("Protein")

    def _translations_url(self):
        return reverse("categories:category-translation-list", kwargs={"category_slug": self.category.slug})

    def test_add_translation_requires_admin(self):
        response = self.client.post(self._translations_url(), {"language": "ru", "name": "Протеин"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_add_translation(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self._translations_url(), {"language": "ru", "name": "Протеин"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        detail = self.client.get(reverse("categories:category-list"), {"lang": "ru"})
        matched = next(c for c in detail.data["results"] if c["slug"] == "protein")
        self.assertEqual(matched["name"], "Протеин")
        self.assertTrue(matched["translation_available"])

    def test_missing_translation_falls_back_and_flags_it(self):
        # Only "en" exists (from make_category) -- requesting "ru" should
        # fall back to "en" and say so.
        response = self.client.get(reverse("categories:category-list"), {"lang": "ru"})
        matched = next(c for c in response.data["results"] if c["slug"] == "protein")
        self.assertEqual(matched["name"], "Protein")
        self.assertEqual(matched["language"], "en")
        self.assertFalse(matched["translation_available"])
        self.assertEqual(matched["requested_language"], "ru")

    def test_duplicate_language_translation_rejected(self):
        self.client.force_authenticate(user=self.admin)
        # "en" already exists for this category via make_category().
        response = self.client.post(self._translations_url(), {"language": "en", "name": "Protein 2"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
