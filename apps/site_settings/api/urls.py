from django.urls import path

from .views import SiteSettingsView

app_name = "site_settings"

urlpatterns = [
    path("", SiteSettingsView.as_view(), name="site-settings"),
]
