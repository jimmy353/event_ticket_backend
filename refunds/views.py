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


def _event_start_datetime(order: Order):
    """
    Your Order model links to ticket_type -> event.
    We assume Event has start_date (DateTimeField).
    """
    try:
        return order.ticket_type.event.start_date
    except Exception:
        return None


def _refund_allowed(order: Order):
    start_dt = _event_start_datetime(order)
    if not start_dt:
        return False, "Event start date missing."

    # ✅ Refund allowed only if more than 24 hours before event
    if start_dt - timezone.now() <= timedelta(hours=24):
        return False, "Refund is only accepted until 24 hours before the event."

    return True, None


# ===============================
# USER REQUEST REFUND
# POST /api/refunds/request/
# body: { "order_id": 1, "reason": "optional" }
# ===============================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def request_refund(request):
    order_id = request.data.get("order_id")
    reason = request.data.get("reason")

    if not order_id:
        return Response({"error": "order_id required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        order = (
            Order.objects
            .select_for_update()
            .select_related("ticket_type", "ticket_type__event")
            .get(id=order_id, user=request.user)
        )
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    if order.status != "paid":
        return Response({"error": "Only paid orders can be refunded."}, status=400)

    # already requested?
    if hasattr(order, "refund"):
        return Response({"error": "Refund already requested for this order."}, status=400)

    ok, msg = _refund_allowed(order)
    if not ok:
        return Response({"error": msg}, status=400)

    # ✅ cancel tickets for this order (best practice)
    Ticket.objects.filter(
        user=request.user,
        ticket_type=order.ticket_type,
        is_cancelled=False
    ).order_by("-created_at")[:order.quantity].update(
        is_cancelled=True,
        cancelled_at=timezone.now(),
    )

    # ✅ update order status
    order.status = "refund_requested"
    order.save(update_fields=["status"])

    refund = Refund.objects.create(
        order=order,
        amount=order.total_amount,
        reason=reason,
        provider=order.payment_method,  # MOMO / MGURUSH
        status="pending",
    )

    return Response(
        {
            "message": "Refund requested. Refund may take 3 to 7 days to be processed in MoMo.",
            "refund_id": refund.id,
            "status": refund.status,
            "order_id": order.id,
            "amount": float(refund.amount),
        },
        status=200
    )


# ===============================
# ORGANIZER LIST REFUNDS
# GET /api/refunds/organizer/?event=<id>
# ===============================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_refunds(request):
    event_id = request.GET.get("event")

    qs = (
        Refund.objects
        .select_related(
            "order",
            "order__user",
            "order__ticket_type",
            "order__ticket_type__event",
        )
        .filter(order__ticket_type__event__organizer=request.user)
        .order_by("-created_at")
    )

    if event_id:
        qs = qs.filter(order__ticket_type__event_id=event_id)

    data = []
    for r in qs:
        o = r.order
        ev = o.ticket_type.event
        data.append({
            "id": r.id,
            "status": r.status,
            "amount": float(r.amount),
            "created_at": r.created_at,
            "approved_at": r.approved_at,
            "order_id": o.id,
            "customer_email": o.user.email if o.user else None,
            "event_id": ev.id,
            "event_title": ev.title,
            "ticket_type_name": o.ticket_type.name,
            "provider": r.provider,
            "provider_reference": r.provider_reference,
        })

    return Response(data, status=200)


# ===============================
# ADMIN APPROVE REFUND
# POST /api/refunds/admin/<id>/approve/
# body: { "note": "optional", "provider_reference": "optional" }
# ===============================
@api_view(["POST"])
@permission_classes([IsAdminUser])
@transaction.atomic
def admin_approve_refund(request, refund_id):
    note = request.data.get("note")
    provider_reference = request.data.get("provider_reference")

    try:
        refund = Refund.objects.select_for_update().select_related(
            "order", "order__ticket_type", "order__ticket_type__event"
        ).get(id=refund_id)
    except Refund.DoesNotExist:
        return Response({"error": "Refund not found"}, status=404)

    if refund.status not in ["pending"]:
        return Response({"error": "Only pending refunds can be approved."}, status=400)

    # ✅ mark approved
    refund.mark_approved(note=note)
    if provider_reference:
        refund.provider_reference = provider_reference
        refund.save(update_fields=["provider_reference"])

    # ✅ update order (you can later set to refunded after real MoMo callback)
    order = refund.order
    order.status = "refunded"
    order.save(update_fields=["status"])

    refund.status = "refunded"
    refund.refunded_at = timezone.now()
    refund.save(update_fields=["status", "refunded_at"])

    return Response(
        {"message": "Refund approved and marked as refunded.", "refund_id": refund.id},
        status=200
    )