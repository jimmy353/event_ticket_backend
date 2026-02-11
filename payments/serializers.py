from rest_framework import serializers
from tickets.models import TicketType


class TicketPurchaseItemSerializer(serializers.Serializer):
    ticket_type_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_ticket_type_id(self, value):
        if not TicketType.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid ticket type.")
        return value
