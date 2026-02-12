from rest_framework import serializers
from .models import Event


class EventListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    organizer_name = serializers.CharField(source="organizer.email", read_only=True)

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
        request = self.context.get("request")
        if obj.image and request:
            url = request.build_absolute_uri(obj.image.url)
            return url.replace("http://", "https://")
        return None


class OrganizerEventSerializer(serializers.ModelSerializer):
    image = serializers.Serializer.MethodField()

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
        request = self.context.get("request")
        if obj.image and request:
            url = request.build_absolute_uri(obj.image.url)
            return url.replace("http://", "https://")
        return None


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