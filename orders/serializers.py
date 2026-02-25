from rest_framework import serializers
from .models import Order


# ============================================
# DEFAULT ORDER SERIALIZER (ADMIN / INTERNAL)
# ============================================
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


# ==================================================
# MY ORDERS SERIALIZER (MOBILE APP / REFUND LOGIC)
# ==================================================
class MyOrderSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(
        source="ticket_type.event.title",
        read_only=True
    )

    event_start_date = serializers.DateTimeField(
        source="ticket_type.event.start_date",
        read_only=True
    )

    ticket_type_name = serializers.CharField(
        source="ticket_type.name",
        read_only=True
    )

    event_id = serializers.IntegerField(
        source="ticket_type.event.id",
        read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "quantity",
            "total_amount",
            "created_at",

            # 🔥 IMPORTANT FOR REFUND SYSTEM
            "event_id",
            "event_title",
            "event_start_date",
            "ticket_type_name",
        ]