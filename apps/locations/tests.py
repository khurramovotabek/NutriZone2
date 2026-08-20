from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import City, Country, Region

User = get_user_model()


class LocationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="AdminPass123!")
        self.country = Country.objects.create(name="Uzbekistan", code="UZ")
        self.region = Region.objects.create(country=self.country, name="Tashkent Region")
        self.city = City.objects.create(region=self.region, name="Tashkent")

    def test_list_countries_public(self):
        response = self.client.get(reverse("locations:country-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_regions_filterable_by_country(self):
        response = self.client.get(reverse("locations:region-list"), {"country": str(self.country.id)})
        self.assertEqual(response.data["count"], 1)

    def test_cities_filterable_by_region(self):
        response = self.client.get(reverse("locations:city-list"), {"region": str(self.region.id)})
        self.assertEqual(response.data["count"], 1)

    def test_create_requires_admin(self):
        response = self.client.post(reverse("locations:country-list"), {"name": "Kazakhstan", "code": "KZ"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
