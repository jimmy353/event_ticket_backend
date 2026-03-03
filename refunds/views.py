from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from orders.models import Order
from tickets.models import Ticket
from .models import Refund


# =====================================================
# 24 HOUR RULE
# =====================================================
def _refund_allowed(order):
    event_start = order.ticket_type.event.start_date
    now = timezone.now()

    cutoff_time = event_start - timedelta(hours=24)

    if now >= cutoff_time:
        return False, "Refund not allowed within 24 hours of the event."

    return True, None 


# =====================================================
# USER REQUEST REFUND
# POST /api/refunds/request/
# =====================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def request_refund(request):
    order_id = request.data.get("order_id")
    reason = request.data.get("reason")

    if not order_id:
        return Response({"error": "order_id required"}, status=400)

    try:
        order = (
            Order.objects
            .select_related("ticket_type", "ticket_type__event")
            .get(id=order_id, user=request.user)
        )
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    if order.status != "paid":
        return Response({"error": "Only paid orders can be refunded."}, status=400)

    # Already has refund?
    if hasattr(order, "refund"):
        return Response({"error": "Refund already requested."}, status=400)

    allowed, message = _refund_allowed(order)
    if not allowed:
        return Response({"error": message}, status=400)

    # Cancel tickets
    Ticket.objects.filter(
        user=request.user,
        ticket_type=order.ticket_type,
        is_cancelled=False,
    ).update(
        is_cancelled=True,
        cancelled_at=timezone.now(),
    )

    # Update order
    order.status = "refund_requested"
    order.save(update_fields=["status"])

    # Create refund
    refund = Refund.objects.create(
        order=order,
        amount=order.total_amount,
        reason=reason,
        provider=order.payment_method,
        status="requested",
    )

    return Response({
        "message": "Refund requested. Processing may take 3–7 days.",
        "refund_id": refund.id,
        "reference": refund.reference,
        "status": refund.status,
        "amount": float(refund.amount),
    })


# =====================================================
# ORGANIZER REFUND LIST
# GET /api/refunds/organizer/?event=<id>
# =====================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_refunds(request):
    event_id = request.GET.get("event")

    try:
        refunds = (
            Refund.objects
            .select_related(
                "order",
                "order__user",
                "order__ticket_type",
                "order__ticket_type__event"
            )
            .filter(order__ticket_type__event__organizer=request.user)
            .order_by("-requested_at")
        )

        if event_id:
            refunds = refunds.filter(order__ticket_type__event_id=event_id)

        data = []

        for r in refunds:
            order = r.order
            event = order.ticket_type.event

            data.append({
                "id": r.id,
                "reference": r.reference,
                "status": r.status,
                "amount": float(r.amount),

                "requested_at": r.requested_at,
                "approved_at": r.approved_at,
                "expected_paid_from": r.expected_paid_from,
                "expected_paid_to": r.expected_paid_to,
                "paid_at": r.paid_at,

                "order_id": order.id,
                "customer_email": order.user.email if order.user else None,

                "event_id": event.id,
                "event_title": event.title,
                "ticket_type_name": order.ticket_type.name,

                "provider": r.provider,
                "provider_reference": r.provider_reference,
            })

        return Response(data)

    except Exception as e:
        return Response(
            {"error": f"Server error: {str(e)}"},
            status=500
        )


# =====================================================
# ADMIN APPROVE REFUND
# POST /api/refunds/admin/<id>/approve/
# =====================================================
@api_view(["POST"])
@permission_classes([IsAdminUser])
@transaction.atomic
def admin_approve_refund(request, refund_id):
    try:
        refund = Refund.objects.get(id=refund_id)
    except Refund.DoesNotExist:
        return Response({"error": "Refund not found"}, status=404)

    if refund.status != "requested":
        return Response({"error": "Refund must be requested first."}, status=400)

    refund.status = "approved"
    refund.approved_at = timezone.now()
    refund.save(update_fields=["status", "approved_at"])

    # Move to processing stage (3–7 days window)
    refund.mark_processing()

    return Response({
        "message": "Refund approved and now processing.",
        "status": refund.status,
        "expected_paid_from": refund.expected_paid_from,
        "expected_paid_to": refund.expected_paid_to,
    })


# =====================================================
# ADMIN MARK AS PAID
# POST /api/refunds/admin/<id>/mark-paid/
# =====================================================
@api_view(["POST"])
@permission_classes([IsAdminUser])
@transaction.atomic
def admin_mark_refund_paid(request, refund_id):
    provider_reference = request.data.get("provider_reference")

    try:
        refund = Refund.objects.get(id=refund_id)
    except Refund.DoesNotExist:
        return Response({"error": "Refund not found"}, status=404)

    if refund.status != "processing":
        return Response({"error": "Refund must be processing first."}, status=400)

    refund.mark_paid(provider_reference=provider_reference)

    # Update order
    refund.order.status = "refunded"
    refund.order.save(update_fields=["status"])

    return Response({
        "message": "Refund marked as paid.",
        "status": refund.status,
    })