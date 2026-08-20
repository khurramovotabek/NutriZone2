"""Read-query helpers for the media library."""

from django.db.models import QuerySet

from .models import MediaFile


def media_files_in_folder(folder: str) -> QuerySet[MediaFile]:
    return MediaFile.objects.filter(folder=folder)
