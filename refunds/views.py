from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import RefundRequest
from .serializers import RefundRequestSerializer
from orders.models import Order
from tickets.models import Ticket
from payments.models import Payment


# ===============================
# USER CREATE REFUND REQUEST
# ===============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_refund_request(request):
    order_id = request.data.get("order_id")
    reason = request.data.get("reason", "")

    if not order_id:
        return Response(
            {"error": "order_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        order = Order.objects.select_related(
            "ticket_type",
            "ticket_type__event"
        ).get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response(
            {"error": "Order not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if order.status != "paid":
        return Response(
            {"error": "Only paid orders can request refund"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if RefundRequest.objects.filter(order=order).exists():
        return Response(
            {"error": "Refund request already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )

    refund = RefundRequest.objects.create(
        user=request.user,
        order=order,
        reason=reason,
        status="pending"
    )

    return Response(
        RefundRequestSerializer(refund).data,
        status=status.HTTP_201_CREATED
    )


# ===============================
# ORGANIZER VIEW REFUND REQUESTS
# ===============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_refund_requests(request):
    refunds = RefundRequest.objects.filter(
        order__ticket_type__event__organizer=request.user
    ).order_by("-created_at")

    serializer = RefundRequestSerializer(refunds, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ===============================
# ORGANIZER APPROVE REFUND
# ===============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_refund(request, refund_id):
    try:
        refund = RefundRequest.objects.select_related(
            "order",
            "order__ticket_type",
            "order__ticket_type__event"
        ).get(id=refund_id)
    except RefundRequest.DoesNotExist:
        return Response(
            {"error": "Refund request not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    order = refund.order
    event = order.ticket_type.event

    # 🔐 Organizer security
    if event.organizer != request.user:
        return Response(
            {"error": "Not allowed"},
            status=status.HTTP_403_FORBIDDEN
        )

    if refund.status != "pending":
        return Response(
            {"error": "Refund already reviewed"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ❌ Block if tickets already used
    used_ticket_exists = Ticket.objects.filter(
        user=order.user,
        ticket_type=order.ticket_type,
        is_used=True
    ).exists()

    if used_ticket_exists:
        refund.status = "rejected"
        refund.reviewed_at = timezone.now()
        refund.save(update_fields=["status", "reviewed_at"])

        return Response(
            {"error": "Refund rejected. Ticket already used."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ✅ Mark payment refunded
    payment = Payment.objects.filter(order=order, status="success").first()
    if payment:
        payment.status = "refunded"
        payment.save(update_fields=["status"])

    # ✅ Cancel tickets
    tickets = Ticket.objects.filter(
        user=order.user,
        ticket_type=order.ticket_type,
        is_cancelled=False
    ).order_by("-created_at")[:order.quantity]

    for t in tickets:
        t.is_cancelled = True
        t.cancelled_at = timezone.now()
        t.save(update_fields=["is_cancelled", "cancelled_at"])

    # ✅ Restore stock
    order.ticket_type.quantity_sold = max(
        order.ticket_type.quantity_sold - order.quantity,
        0
    )
    order.ticket_type.save(update_fields=["quantity_sold"])

    # ✅ Update order status
    order.status = "refunded"
    order.save(update_fields=["status"])

    # ✅ Update refund request
    refund.status = "approved"
    refund.reviewed_at = timezone.now()
    refund.save(update_fields=["status", "reviewed_at"])

    return Response(
        {
            "message": "Refund approved successfully",
            "refund": RefundRequestSerializer(refund).data
        },
        status=status.HTTP_200_OK
    )


# ===============================
# ORGANIZER REJECT REFUND
# ===============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_refund(request, refund_id):
    try:
        refund = RefundRequest.objects.select_related(
            "order",
            "order__ticket_type",
            "order__ticket_type__event"
        ).get(id=refund_id)
    except RefundRequest.DoesNotExist:
        return Response(
            {"error": "Refund request not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    order = refund.order
    event = order.ticket_type.event

    # 🔐 Organizer security
    if event.organizer != request.user:
        return Response(
            {"error": "Not allowed"},
            status=status.HTTP_403_FORBIDDEN
        )

    if refund.status != "pending":
        return Response(
            {"error": "Refund already reviewed"},
            status=status.HTTP_400_BAD_REQUEST
        )

    refund.status = "rejected"
    refund.reviewed_at = timezone.now()
    refund.save(update_fields=["status", "reviewed_at"])

    return Response(
        {
            "message": "Refund rejected",
            "refund": RefundRequestSerializer(refund).data
        },
        status=status.HTTP_200_OK
    )