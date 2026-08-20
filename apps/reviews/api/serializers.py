from django.core.validators import MaxValueValidator, MinValueValidator
from rest_framework import serializers

from ..models import Review, ReviewImage, ReviewReply, ReviewReport, ReviewVideo


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ["id", "image", "sort_order"]
        read_only_fields = ["id"]


class ReviewVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewVideo
        fields = ["id", "video", "thumbnail", "sort_order"]
        read_only_fields = ["id"]


class ReviewReplySerializer(serializers.ModelSerializer):
    """Admin's reply, shown under the customer's review with an Admin badge
    on the frontend (is_admin_reply is always True here -- kept explicit in
    the payload so the frontend doesn't have to assume)."""

    admin_username = serializers.CharField(source="admin_user.username", read_only=True, default="NutriZone")
    is_admin_reply = serializers.SerializerMethodField()

    class Meta:
        model = ReviewReply
        fields = ["id", "admin_username", "is_admin_reply", "message", "created_at"]
        read_only_fields = fields

    def get_is_admin_reply(self, obj):
        return True


class ReviewSerializer(serializers.ModelSerializer):
    """Read representation -- shown in the product page's review list."""

    username = serializers.CharField(source="user.username", read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)
    videos = ReviewVideoSerializer(many=True, read_only=True)
    replies = ReviewReplySerializer(many=True, read_only=True)
    helpful_count = serializers.IntegerField(read_only=True, default=0)
    is_marked_helpful_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "username",
            "rating",
            "comment",
            "is_verified_purchase",
            "images",
            "videos",
            "replies",
            "helpful_count",
            "is_marked_helpful_by_me",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_is_marked_helpful_by_me(self, obj):
        helpful_ids = self.context.get("helpful_review_ids", set())
        return obj.id in helpful_ids


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = serializers.CharField(required=False, allow_blank=True, default="")
    images = serializers.ListField(
        child=serializers.ImageField(), required=False, allow_empty=True, max_length=6
    )
    videos = serializers.ListField(
        child=serializers.FileField(), required=False, allow_empty=True, max_length=2
    )


class ReviewUpdateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(required=False, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = serializers.CharField(required=False, allow_blank=True)


class RatingSummarySerializer(serializers.Serializer):
    average = serializers.FloatField(allow_null=True)
    total = serializers.IntegerField()
    distribution = serializers.DictField(child=serializers.IntegerField())


class ReviewReplyCreateSerializer(serializers.Serializer):
    message = serializers.CharField()


class ReviewReportCreateSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=ReviewReport.Reason.choices)
    comment = serializers.CharField(required=False, allow_blank=True, default="")
