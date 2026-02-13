from rest_framework import serializers
from .models import Event


class EventListSerializer(serializers.ModelSerializer):
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


class OrganizerEventSerializer(serializers.ModelSerializer):
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