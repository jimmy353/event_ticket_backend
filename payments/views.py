# payments/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from orders.models import Order
from .models import Payment

from tickets.models import Ticket
from tickets.utils import generate_qr_code


# ===============================
# INITIATE PAYMENT (USER)
# ===============================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """
    Expected request body:
    {
        "order_id": 1,
        "provider": "momo" or "mgurush",
        "phone": "0922458583"
    }
    """

    order_id = request.data.get("order_id")
    provider = request.data.get("provider")
    phone_number = request.data.get("phone_number") or request.data.get("phone")

    if not order_id:
        return Response({"error": "order_id required"}, status=status.HTTP_400_BAD_REQUEST)

    if not provider:
        return Response({"error": "provider required"}, status=status.HTTP_400_BAD_REQUEST)

    if provider not in ["momo", "mgurush"]:
        return Response(
            {"error": "provider must be momo or mgurush"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not phone_number:
        return Response({"error": "phone_number required"}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        try:
            order = (
                Order.objects
                .select_for_update()
                .select_related("ticket_type", "ticket_type__event")
                .get(id=order_id, user=request.user)
            )
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        # ✅ If already paid, return existing tickets
        if order.status == "paid":
            latest_tickets = (
                Ticket.objects
                .filter(user=request.user, ticket_type=order.ticket_type)
                .order_by("-created_at")[:order.quantity]
            )

            return Response(
                {
                    "message": "Order already paid",
                    "order_id": order.id,
                    "quantity": order.quantity,
                    "tickets": [
                        {
                            "ticket_code": str(t.ticket_code),
                            "qr_code": request.build_absolute_uri(t.qr_code.url) if t.qr_code else None,
                        }
                        for t in reversed(list(latest_tickets))
                    ],
                },
                status=status.HTTP_200_OK,
            )

        # lock ticket type
        ticket_type = (
            order.ticket_type.__class__.objects
            .select_for_update()
            .get(id=order.ticket_type.id)
        )

        available = ticket_type.quantity_total - ticket_type.quantity_sold
        if order.quantity > available:
            return Response(
                {"error": f"Only {available} tickets available"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Create payment record
        payment = Payment.objects.create(
            order=order,
            provider=provider,
            phone=phone_number,
            amount=order.total_amount,
            status="pending",
        )

        # ===========================
        # SIMULATE PAYMENT SUCCESS
        # ===========================
        payment.status = "success"
        payment.save(update_fields=["status"])

        order.status = "paid"
        order.payment_status = "PAID"
        order.payment_method = provider.upper()
        order.save(update_fields=["status", "payment_status", "payment_method"])

        ticket_type.quantity_sold += order.quantity
        ticket_type.save(update_fields=["quantity_sold"])

        created_tickets = []
        for _ in range(order.quantity):
            # ✅ IMPORTANT: link ticket to the order (refund system needs this)
            ticket = Ticket.objects.create(
                user=request.user,
                ticket_type=ticket_type,
                order=order,  # 🔥 THIS IS THE FIX
            )

            ticket.qr_code.save(
                f"{ticket.ticket_code}.png",
                generate_qr_code(str(ticket.ticket_code))
            )
            ticket.save()

            created_tickets.append(ticket)

    return Response(
        {
            "message": "Payment successful",
            "payment_id": payment.id,
            "order_id": order.id,
            "quantity": order.quantity,
            "tickets": [
                {
                    "ticket_code": str(t.ticket_code),
                    "qr_code": request.build_absolute_uri(t.qr_code.url) if t.qr_code else None,
                }
                for t in created_tickets
            ],
        },
        status=status.HTTP_200_OK,
    )


# ===============================
# ORGANIZER PAYMENTS LIST
# ===============================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_payments(request):
    """
    GET /api/payments/organizer/?event=<event_id>
    """
    event_id = request.GET.get("event")

    qs = (
        Payment.objects
        .select_related(
            "order",
            "order__user",
            "order__ticket_type",
            "order__ticket_type__event"
        )
        .filter(
            order__ticket_type__event__organizer=request.user,
        )
        .order_by("-created_at")
    )

    if event_id:
        qs = qs.filter(order__ticket_type__event_id=event_id)

    data = []
    for p in qs:
        order = p.order
        event = order.ticket_type.event

        # ✅ payout/refund status logic (frontend will now update correctly)
        if order.status == "refunded":
            payout_status = "refunded"
        elif order.status == "refund_requested":
            payout_status = "refund_requested"
        elif order.is_withdrawn:
            payout_status = "paid"
        else:
            payout_status = "unpaid"

        # ✅ If order is refunded, still show it (so organizer sees it),
        # but it will NOT count as withdrawable anymore.
        data.append({
            "id": p.id,
            "provider": p.provider,
            "phone": p.phone,
            "status": p.status,
            "created_at": p.created_at,

            "order_id": order.id,
            "quantity": order.quantity,
            "customer_email": order.user.email if order.user else None,

            "ticket_type_name": order.ticket_type.name,
            "event_id": event.id,
            "event_title": event.title,

            "amount": float(order.total_amount),
            "commission": float(order.commission_amount),
            "organizer_amount": float(order.organizer_amount),

            "payout_status": payout_status,
        })

    return Response(data, status=status.HTTP_200_OK)