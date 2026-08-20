import os

from rest_framework import serializers

from ..models import MediaFile

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ["id", "file", "folder", "original_name", "content_type", "size", "created_at"]
        read_only_fields = ["id", "original_name", "content_type", "size", "created_at"]

    def validate_file(self, value):
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
            )
        if value.size > MAX_UPLOAD_SIZE:
            raise serializers.ValidationError("File is too large. Maximum size is 10MB.")
        return value

    def validate_folder(self, value):
        # Prevent path traversal via a crafted folder name.
        safe = "".join(c for c in value if c.isalnum() or c in ("-", "_")).strip()
        return safe or "misc"

    def create(self, validated_data):
        file_obj = validated_data["file"]
        validated_data.setdefault("content_type", getattr(file_obj, "content_type", ""))
        return super().create(validated_data)
