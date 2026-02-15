from rest_framework import serializers
from .models import Event


def fix_cloudinary_url(field):
    if not field:
        return None

    try:
        url = field.build_url()
        url = url.replace("http://", "https://")
        return url
    except Exception:
        return None


class EventListSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source="organizer.email", read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "location",
            "category",
            "start_date",
            "end_date",
            "image",
            "organizer_name",
        ]

    def get_image(self, obj):
        return fix_cloudinary_url(obj.image)


class OrganizerEventSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "location",
            "category",
            "start_date",
            "end_date",
            "image",
        ]

    def get_image(self, obj):
        return fix_cloudinary_url(obj.image)


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "location",
            "category",
            "start_date",
            "end_date",
            "image",
        ]