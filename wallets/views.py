from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import OrganizerWallet
from .serializers import OrganizerWalletSerializer


class OrganizerWalletAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, _ = OrganizerWallet.objects.get_or_create(owner=request.user)
        serializer = OrganizerWalletSerializer(wallet)
        return Response(serializer.data)
