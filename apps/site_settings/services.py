from .models import SiteSettings


class SiteSettingsService:
    @staticmethod
    def get_settings() -> SiteSettings:
        return SiteSettings.load()
