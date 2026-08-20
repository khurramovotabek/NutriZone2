from rest_framework.routers import DefaultRouter

from .views import CityViewSet, CountryViewSet, RegionViewSet

app_name = "locations"

router = DefaultRouter()
router.register("countries", CountryViewSet, basename="country")
router.register("regions", RegionViewSet, basename="region")
router.register("cities", CityViewSet, basename="city")

urlpatterns = router.urls
