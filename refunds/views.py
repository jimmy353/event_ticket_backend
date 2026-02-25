from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from orders.models import Order
from tickets.models import Ticket, TicketType
from .models import Refund
from .serializers import RefundSerializer


REFUND_CUTOFF_HOURS = 24  # ✅ accepted until 1 day before event


def _event_allows_refund(event):
    if not event:
        return False
    # Use event.start_date or event.start_datetime depending on your Event model
    start = getattr(event, "start_date", None) or getattr(event, "start_datetime", None)
    if not start:
        return False
    # if it's a date, convert to datetime at midnight
    if hasattr(start, "year") and not hasattr(start, "hour"):
        start = timezone.make_aware(timezone.datetime(start.year, start.month, start.day))
    return (start - timezone.now()) >= timedelta(hours=REFUND_CUTOFF_HOURS)


# =====================================================
# 1) USER: REQUEST REFUND
# =====================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_refund(request):
    user = request.user
    order_id = request.data.get("order_id")
    reason = request.data.get("reason")

    if not order_id:
        return Response({"error": "order_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        order = Order.objects.select_related("ticket_type", "ticket_type__event").get(id=order_id, user=user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    if order.status != "paid":
        return Response({"error": "Only paid orders can be refunded"}, status=status.HTTP_400_BAD_REQUEST)

    if order.is_withdrawn:
        return Response({"error": "Refund not allowed. Funds already withdrawn by organizer."},
                        status=status.HTTP_400_BAD_REQUEST)

    event = order.ticket_type.event
    if not _event_allows_refund(event):
        return Response({"error": "Refund allowed only until 1 day before event starts."},
                        status=status.HTTP_400_BAD_REQUEST)

    # Prevent duplicate
    if Refund.objects.filter(order=order).exists():
        return Response({"error": "Refund already requested for this order."}, status=status.HTTP_400_BAD_REQUEST)

    refund = Refund.objects.create(
        order=order,
        amount=order.total_amount,
        status="requested",
        reason=reason,
        provider=(order.payment_method or "").upper(),  # MOMO / MGURUSH
    )

    order.status = "refund_requested"
    order.save(update_fields=["status"])

    return Response(
        {
            "message": "Refund requested successfully.",
            "reference": refund.reference,
            "amount": float(refund.amount),
            "note": "Refund can take 3 to 7 days to be processed in MoMo.",
        },
        status=status.HTTP_201_CREATED,
    )


# =====================================================
# 2) USER: MY REFUNDS
# =====================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_refunds(request):
    qs = Refund.objects.select_related("order").filter(order__user=request.user).order_by("-requested_at")
    return Response(RefundSerializer(qs, many=True).data, status=status.HTTP_200_OK)


# =====================================================
# 3) ADMIN: LIST REFUNDS
# =====================================================
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_refunds(request):
    qs = Refund.objects.select_related("order", "order__user").order_by("-requested_at")
    return Response(RefundSerializer(qs, many=True).data, status=status.HTTP_200_OK)


# =====================================================
# 4) ADMIN: APPROVE REFUND
# =====================================================
@api_view(["POST"])
@permission_classes([IsAdminUser])
@transaction.atomic
def approve_refund(request, reference):
    admin_note = request.data.get("admin_note")
    provider_reference = request.data.get("provider_reference")  # optional

    try:
        refund = Refund.objects.select_for_update().select_related("order", "order__ticket_type").get(reference=reference)
    except Refund.DoesNotExist:
        return Response({"error": "Refund not found"}, status=status.HTTP_404_NOT_FOUND)

    order = Order.objects.select_for_update().select_related("ticket_type").get(id=refund.order_id)
    ticket_type = TicketType.objects.select_for_update().get(id=order.ticket_type_id)

    if refund.status not in ["requested", "approved", "processing"]:
        return Response({"error": "Refund already finalized."}, status=status.HTTP_400_BAD_REQUEST)

    # Mark as processing with 3-7 days ETA
    refund.status = "approved"
    refund.approved_at = timezone.now()
    refund.admin_note = admin_note
    refund.save(update_fields=["status", "approved_at", "admin_note"])

    refund.mark_processing()

    # ✅ Cancel ONLY tickets for this order if order field exists
    cancelled_qs = Ticket.objects.filter(order=order, is_cancelled=False)

    cancelled_count = cancelled_qs.count()

    if cancelled_count == 0:
        # Fallback for old tickets without order link:
        # cancel latest N tickets for same user + ticket_type
        fallback = (
            Ticket.objects.filter(user=order.user, ticket_type=ticket_type, is_cancelled=False)
            .order_by("-created_at")[: order.quantity]
        )
        cancelled_count = fallback.count()
        for t in fallback:
            t.is_cancelled = True
            t.cancelled_at = timezone.now()
            t.save(update_fields=["is_cancelled", "cancelled_at"])
    else:
        cancelled_qs.update(is_cancelled=True, cancelled_at=timezone.now())

    # ✅ Fix sold count safely
    ticket_type.quantity_sold = max(ticket_type.quantity_sold - cancelled_count, 0)
    ticket_type.save(update_fields=["quantity_sold"])

    # ✅ Update order status
    order.status = "refunded"
    order.save(update_fields=["status"])

    # You can later call refund.mark_paid(...) after real MoMo refund success
    # For now (simulation): mark paid instantly if you want:
    # refund.mark_paid(provider_reference=provider_reference)

    if provider_reference:
        refund.provider_reference = provider_reference
        refund.save(update_fields=["provider_reference"])

    return Response(
        {
            "message": "Refund approved and set to processing.",
            "reference": refund.reference,
            "expected_paid_from": refund.expected_paid_from,
            "expected_paid_to": refund.expected_paid_to,
        },
        status=status.HTTP_200_OK,
    )


# =====================================================
# 5) ADMIN: MARK REFUND PAID (OPTIONAL)
# =====================================================
@api_view(["POST"])
@permission_classes([IsAdminUser])
def mark_refund_paid(request, reference):
    provider_reference = request.data.get("provider_reference")

    try:
        refund = Refund.objects.get(reference=reference)
    except Refund.DoesNotExist:
        return Response({"error": "Refund not found"}, status=status.HTTP_404_NOT_FOUND)

    refund.mark_paid(provider_reference=provider_reference)
    return Response({"message": "Refund marked as paid.", "reference": refund.reference}, status=status.HTTP_200_OK)