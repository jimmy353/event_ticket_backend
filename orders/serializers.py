from rest_framework import serializers
from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "ticket_type",
            "quantity",
            "total_amount",
            "commission_amount",
            "organizer_amount",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "commission_amount",
            "organizer_amount",
            "status",
            "created_at",
        ]