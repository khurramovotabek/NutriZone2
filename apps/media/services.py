from .models import MediaFile


class MediaService:
    @staticmethod
    def list_folders() -> list[str]:
        return list(MediaFile.objects.values_list("folder", flat=True).distinct())
