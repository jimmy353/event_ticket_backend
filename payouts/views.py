from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Payout
from .serializers import PayoutSerializer
from orders.models import Order
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
# 2️⃣ REQUEST WITHDRAWAL (SECURE VERSION)
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

    # Get PAID orders only
    orders = Order.objects.filter(
        ticket_type__event=event,
        status="paid",
        is_withdrawn=False
    )

    if not orders.exists():
        return Response(
            {"error": "No earnings available."},
            status=status.HTTP_400_BAD_REQUEST
        )

    total = orders.aggregate(
        total=Sum("organizer_amount")
    )["total"] or 0

    payout = Payout.objects.create(
        organizer=user,
        event=event,
        amount=total,
        note=f"Payout request for {event.title}"
    )

    # Attach exact orders to payout
    payout.orders.set(orders)

    return Response({
        "message": "Withdrawal request submitted successfully.",
        "total": float(total),
        "reference": payout.reference,
    })


# =====================================================
# 3️⃣ ADMIN APPROVE PAYOUT (USING REFERENCE)
# =====================================================

@api_view(["POST"])
@permission_classes([permissions.IsAdminUser])
def approve_payout(request, reference):
    try:
        payout = Payout.objects.get(reference=reference)
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

    # 1️⃣ Mark payout paid
    payout.mark_paid()

    # 2️⃣ Mark ONLY attached orders withdrawn
    payout.orders.update(is_withdrawn=True)

    # 3️⃣ (Optional safety) unlock wallet if using locked_balance
    from wallets.models import OrganizerWallet

    wallet = OrganizerWallet.objects.filter(
        organizer=payout.organizer
    ).first()

    if wallet:
        wallet.locked_balance -= payout.amount
        wallet.available_balance += payout.amount
        wallet.save(update_fields=["locked_balance", "available_balance"])

    return Response({
        "message": "Payout approved successfully.",
        "reference": payout.reference
    })