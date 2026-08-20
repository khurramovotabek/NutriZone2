from rest_framework import serializers

from ..models import City, Country, Region


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "code", "is_active"]
        read_only_fields = ["id"]


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "country", "name", "is_active"]
        read_only_fields = ["id"]


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "region", "name", "is_active"]
        read_only_fields = ["id"]


class CountryMiniSerializer(serializers.ModelSerializer):
    """Embedded in Brand / Order responses."""

    class Meta:
        model = Country
        fields = ["id", "name", "code"]


class RegionMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "name"]


class CityMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name"]
