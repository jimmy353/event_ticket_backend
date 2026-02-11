from rest_framework import serializers
from .models import Payout


class PayoutSerializer(serializers.ModelSerializer):
    organizer_email = serializers.CharField(source="organizer.email", read_only=True)

    class Meta:
        model = Payout
        fields = [
            "id",
            "organizer",
            "organizer_email",
            "amount",
            "status",
            "note",
            "created_at",
            "paid_at",
        ]
        read_only_fields = ["id", "created_at", "paid_at"]
