from rest_framework import serializers
from .models import OrganizerWallet


class OrganizerWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizerWallet
        fields = [
            "balance",
            "locked_balance",
        ]
