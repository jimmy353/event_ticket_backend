from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from orders.models import Order
from payments.models import Payment
from tickets.models import Ticket
from wallets.models import OrganizerWallet

from .models import Refund


# ===============================
# USER REQUEST REFUND
# ===============================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_refund(request):
    order_id = request.data.get("order_id")
    reason = request.data.get("reason", "")

    if not order_id:
        return Response({"error": "order_id required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        order = Order.objects.select_related("event").get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    if order.status != "paid":
        return Response({"error": "Only paid orders can be refunded"}, status=status.HTTP_400_BAD_REQUEST)

    if getattr(order, "is_withdrawn", False):
        return Response({"error": "Cannot refund an order that was already withdrawn"}, status=status.HTTP_400_BAD_REQUEST)

    # prevent duplicate refund
    if hasattr(order, "refund"):
        return Response({"error": "Refund already requested for this order"}, status=status.HTTP_400_BAD_REQUEST)

    event = order.event

    # ✅ Refund allowed only until 1 day before event start
    if timezone.now() > (event.start_date - timedelta(days=1)):
        return Response(
            {"error": "Refund allowed only up to 1 day before event start"},
            status=status.HTTP_400_BAD_REQUEST
        )

    refund = Refund.objects.create(
        order=order,
        requested_by=request.user,
        reason=reason,
        amount=order.total_amount,
        status="pending",
    )

    # ✅ expected refund date (3–7 days, we’ll set 5 days average)
    refund.set_expected_refund_date()

    return Response(
        {
            "message": "Refund request submitted",
            "refund_status": refund.status,
            "expected_refund_date": refund.expected_refund_date,
        },
        status=status.HTTP_201_CREATED
    )


# ===============================
# ADMIN APPROVE REFUND
# ===============================
@api_view(["POST"])
@permission_classes([IsAdminUser])
@transaction.atomic
def approve_refund(request, order_id):
    try:
        refund = Refund.objects.select_for_update().select_related("order", "order__event").get(order_id=order_id)
    except Refund.DoesNotExist:
        return Response({"error": "Refund not found"}, status=status.HTTP_404_NOT_FOUND)

    if refund.status != "pending":
        return Response({"error": "Refund already processed"}, status=status.HTTP_400_BAD_REQUEST)

    order = refund.order

    # ✅ Safety checks
    if getattr(order, "is_withdrawn", False):
        return Response({"error": "Cannot refund withdrawn order"}, status=status.HTTP_400_BAD_REQUEST)

    # 1️⃣ Mark order refunded
    order.status = "refunded"
    order.save(update_fields=["status"])

    # 2️⃣ Mark payment refunded (if you store payments by order)
    Payment.objects.filter(order=order).update(status="refunded")

    # 3️⃣ Delete tickets issued for this order (if your Ticket model links to order, use that)
    # If Ticket does NOT link to order, we delete by user + ticket_type as fallback
    if hasattr(order, "ticket_type") and order.ticket_type_id:
        Ticket.objects.filter(user=order.user, ticket_type_id=order.ticket_type_id).delete()

    # 4️⃣ Adjust organizer wallet (locked balance reduced)
    wallet, _ = OrganizerWallet.objects.get_or_create(organizer=order.event.organizer)
    wallet.locked_balance = max(wallet.locked_balance - order.organizer_amount, 0)
    wallet.save(update_fields=["locked_balance"])

    # 5️⃣ Mark refund approved (processed later by momo)
    refund.status = "approved"
    refund.save(update_fields=["status"])

    return Response(
        {
            "message": "Refund approved successfully",
            "refund_status": refund.status,
            "expected_refund_date": refund.expected_refund_date,
        },
        status=status.HTTP_200_OK
    )