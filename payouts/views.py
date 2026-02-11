from rest_framework import generics, permissions
from .models import Payout
from .serializers import PayoutSerializer


class MyPayoutsAPIView(generics.ListAPIView):
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payout.objects.filter(organizer=self.request.user).order_by("-created_at")
