from rest_framework import serializers
from .models import Event


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
        if not obj.image:
            return None

        url = str(obj.image.url)

        # Force cloudinary to return safe format for mobile
        url = url.replace("/upload/", "/upload/f_jpg/")

        return url


class OrganizerEventSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "location",
            "start_date",
            "end_date",
            "image",
        ]

    def get_image(self, obj):
        if not obj.image:
            return None

        url = str(obj.image.url)
        url = url.replace("/upload/", "/upload/f_jpg/")
        return url


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