from django.db import models

from apps.shared.models import BaseModel


class Country(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True, help_text="ISO 3166-1 alpha-2/alpha-3 code, e.g. UZ")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name


class Region(BaseModel):
    """State / province / region within a country."""

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="regions")
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["country", "name"], name="unique_region_per_country")]

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class City(BaseModel):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="cities")
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Cities"
        constraints = [models.UniqueConstraint(fields=["region", "name"], name="unique_city_per_region")]

    def __str__(self):
        return f"{self.name}, {self.region.name}"
