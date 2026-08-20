from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.shared.admin_views import nutrizone_dashboard_view

urlpatterns = [
    path("admin/dashboard/", nutrizone_dashboard_view, name="nutrizone-dashboard"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("config.api_v1_urls")),
    # API schema / docs (unversioned -- describes whichever versions exist)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
