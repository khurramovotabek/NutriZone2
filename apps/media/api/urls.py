from rest_framework.routers import DefaultRouter

from .views import MediaFileViewSet

app_name = "media"

router = DefaultRouter()
router.register("", MediaFileViewSet, basename="media")

urlpatterns = router.urls
