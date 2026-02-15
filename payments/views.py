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
                .select_related("ticket_type")
                .get(id=order_id, user=request.user)
            )
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

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
        order.save(update_fields=["status"])

        ticket_type.quantity_sold += order.quantity
        ticket_type.save(update_fields=["quantity_sold"])

        created_tickets = []

        for _ in range(order.quantity):
            ticket = Ticket.objects.create(
                user=request.user,
                ticket_type=ticket_type,
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
    payments = (
        Payment.objects
        .select_related(
            "order",
            "order__user",
            "order__ticket_type",
            "order__ticket_type__event"
        )
        .filter(order__ticket_type__event__organizer=request.user)
        .order_by("-created_at")
    )

    data = []
    for p in payments:
        data.append({
            "id": p.id,
            "provider": p.provider,
            "phone": p.phone,
            "amount": float(p.amount),
            "status": p.status,
            "created_at": p.created_at,

            "order_id": p.order.id,
            "customer_email": p.order.user.email,

            "ticket_type_name": p.order.ticket_type.name,
            "event_title": p.order.ticket_type.event.title,
        })

    return Response(data, status=status.HTTP_200_OK)