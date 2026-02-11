from rest_framework import serializers
from .models import RefundRequest


class RefundRequestSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    event_title = serializers.CharField(source="order.ticket_type.event.title", read_only=True)
    ticket_type = serializers.CharField(source="order.ticket_type.name", read_only=True)
    amount = serializers.DecimalField(source="order.total_amount", max_digits=12, decimal_places=2, read_only=True)
    customer_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = RefundRequest
        fields = [
            "id",
            "order_id",
            "event_title",
            "ticket_type",
            "amount",
            "customer_email",
            "reason",
            "status",
            "created_at",
            "reviewed_at",
        ]