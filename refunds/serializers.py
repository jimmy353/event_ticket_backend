from rest_framework import serializers
from .models import Refund


class RefundSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id", read_only=True)

    class Meta:
        model = Refund
        fields = [
            "id",
            "reference",
            "order_id",
            "amount",
            "status",
            "reason",
            "admin_note",
            "provider",
            "provider_reference",
            "requested_at",
            "approved_at",
            "expected_paid_from",
            "expected_paid_to",
            "paid_at",
        ]