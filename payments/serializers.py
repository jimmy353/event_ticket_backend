from rest_framework import serializers
from tickets.models import TicketType
from .models import SavedPaymentMethod


class TicketPurchaseItemSerializer(serializers.Serializer):
    ticket_type_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_ticket_type_id(self, value):
        if not TicketType.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid ticket type.")
        return value



class SavedPaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = SavedPaymentMethod
        fields = "_all_"
        read_only_fields = ["user"]