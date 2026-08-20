from django.contrib import admin

from .models import City, Country, Region


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_active"]
    search_fields = ["name", "code"]
    list_editable = ["is_active"]


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "is_active"]
    list_filter = ["country", "is_active"]
    search_fields = ["name"]
    autocomplete_fields = ["country"]
    list_editable = ["is_active"]


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["name", "region", "is_active"]
    list_filter = ["region__country", "is_active"]
    search_fields = ["name"]
    autocomplete_fields = ["region"]
    list_editable = ["is_active"]
