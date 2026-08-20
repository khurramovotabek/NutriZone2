from apps.shared.exceptions import ServiceError

from .models import Brand


class BrandService:
    @staticmethod
    def validate_unique_name(name: str, instance: Brand | None = None) -> None:
        qs = Brand.objects.filter(name__iexact=name)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise ServiceError("A brand with this name already exists.", code="duplicate_brand")
