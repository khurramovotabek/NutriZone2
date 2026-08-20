from django.contrib import admin

from .models import MediaFile


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ["original_name", "folder", "size", "uploaded_by", "created_at"]
    list_filter = ["folder"]
    search_fields = ["original_name"]
    readonly_fields = ["size", "content_type", "uploaded_by"]
