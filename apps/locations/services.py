from apps.shared.exceptions import ServiceError

from .models import City, Region


class LocationService:
    @staticmethod
    def validate_region_belongs_to_country(region: Region, country_id) -> None:
        if str(region.country_id) != str(country_id):
            raise ServiceError(
                "Selected region does not belong to the selected country.", code="invalid_region"
            )

    @staticmethod
    def validate_city_belongs_to_region(city: City, region_id) -> None:
        if str(city.region_id) != str(region_id):
            raise ServiceError("Selected city does not belong to the selected region.", code="invalid_city")
