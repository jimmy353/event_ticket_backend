from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Payout
from .serializers import PayoutSerializer
from payments.models import Payment
from events.models import Event


# =====================================================
# 1️⃣ LIST ORGANIZER PAYOUT HISTORY
# =====================================================

class MyPayoutsAPIView(generics.ListAPIView):
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payout.objects.filter(
            organizer=self.request.user
        ).order_by("-created_at")


# =====================================================
# 2️⃣ REQUEST WITHDRAWAL
# =====================================================

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def request_payout(request):
    user = request.user
    event_id = request.data.get("event_id")

    if not event_id:
        return Response(
            {"error": "Event ID is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        event = Event.objects.get(id=event_id, organizer=user)
    except Event.DoesNotExist:
        return Response(
            {"error": "Event not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Prevent duplicate pending payout
    if Payout.objects.filter(
        organizer=user,
        event=event,
        status="pending"
    ).exists():
        return Response(
            {"error": "There is already a pending payout for this event."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get unpaid payments
    payments = Payment.objects.filter(
        event=event,
        payout_status="unpaid"
    )

    if not payments.exists():
        return Response(
            {"error": "No unpaid earnings available."},
            status=status.HTTP_400_BAD_REQUEST
        )

    total = payments.aggregate(
        total=Sum("organizer_amount")
    )["total"] or 0

    if total <= 0:
        return Response(
            {"error": "No earnings available."},
            status=status.HTTP_400_BAD_REQUEST
        )

    payout = Payout.objects.create(
        organizer=user,
        event=event,
        amount=total,
        status="pending"
    )

    payments.update(payout_status="pending")

    return Response({
        "message": "Withdrawal request submitted successfully.",
        "total": total,
        "payout_id": payout.id
    })


# =====================================================
# 3️⃣ ADMIN APPROVE PAYOUT
# =====================================================

@api_view(["POST"])
@permission_classes([permissions.IsAdminUser])
def approve_payout(request, payout_id):
    try:
        payout = Payout.objects.get(id=payout_id)
    except Payout.DoesNotExist:
        return Response(
            {"error": "Payout not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if payout.status != "pending":
        return Response(
            {"error": "Payout already processed."},
            status=status.HTTP_400_BAD_REQUEST
        )

    payout.status = "paid"
    payout.paid_at = timezone.now()
    payout.save()

    # Mark related payments as paid
    Payment.objects.filter(
        event=payout.event,
        payout_status="pending"
    ).update(payout_status="paid")

    return Response({
        "message": "Payout approved successfully."
    })