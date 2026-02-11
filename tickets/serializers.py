from rest_framework import serializers
from .models import Ticket, TicketType


class TicketTypeSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source="event.title", read_only=True)

    class Meta:
        model = TicketType
        fields = ["id", "event", "event_title", "name", "price", "quantity_total", "quantity_sold"]


class TicketSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    event = serializers.CharField(source="ticket_type.event.title", read_only=True)
    ticket_type_name = serializers.CharField(source="ticket_type.name", read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "ticket_code",
            "user_email",
            "event",
            "ticket_type_name",
            "qr_image",
            "is_used",
            "used_at",
            "created_at",
        ]


