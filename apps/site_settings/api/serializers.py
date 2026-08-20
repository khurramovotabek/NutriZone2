from rest_framework import serializers

from ..models import SiteSettings


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = [
            "id",
            "site_name",
            "currency",
            "contact_phone",
            "contact_email",
            "telegram_link",
            "instagram_link",
            "address",
            "maintenance_mode",
            "logo",
        ]
        read_only_fields = ["id"]
