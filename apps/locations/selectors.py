"""Read-query construction for countries/regions/cities."""

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet

from .models import City, Country, Region


def _restrict_to_active(qs: QuerySet, user: AbstractBaseUser | None) -> QuerySet:
    if not (user and user.is_authenticated and user.is_staff):
        return qs.filter(is_active=True)
    return qs


def visible_countries(user: AbstractBaseUser | None) -> QuerySet[Country]:
    return _restrict_to_active(Country.objects.all(), user)


def visible_regions(user: AbstractBaseUser | None) -> QuerySet[Region]:
    return _restrict_to_active(Region.objects.select_related("country"), user)


def visible_cities(user: AbstractBaseUser | None) -> QuerySet[City]:
    return _restrict_to_active(City.objects.select_related("region"), user)
