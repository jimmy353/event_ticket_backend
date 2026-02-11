from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from orders.models import Order
from .models import Payment

from tickets.models import Ticket
from tickets.utils import generate_qr_code


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

    # ✅ accept both keys
    phone_number = request.data.get("phone_number") or request.data.get("phone")

    if not order_id:
        return Response(
            {"error": "order_id required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not provider:
        return Response(
            {"error": "provider required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if provider not in ["momo", "mgurush"]:
        return Response(
            {"error": "provider must be momo or mgurush"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not phone_number:
        return Response(
            {"error": "phone_number required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ✅ transaction makes it safe (no double creation)
    with transaction.atomic():

        # ✅ lock order row
        try:
            order = (
                Order.objects
                .select_for_update()
                .select_related("ticket_type")
                .get(id=order_id, user=request.user)
            )
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # ✅ If already paid, return the latest tickets (best effort)
        # NOTE: since Ticket has no FK to Order, we return latest tickets for this user+ticket_type.
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

        ticket_type = order.ticket_type

        # ✅ lock ticket_type row too (prevents oversell)
        ticket_type = (
            ticket_type.__class__.objects
            .select_for_update()
            .get(id=ticket_type.id)
        )

        available = ticket_type.quantity_total - ticket_type.quantity_sold
        if order.quantity > available:
            return Response(
                {"error": f"Only {available} tickets available"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Create Payment record
        payment = Payment.objects.create(
            order=order,
            provider=provider,
            phone=phone_number,
            amount=order.total_amount,
            status="pending",
        )

        # ===========================
        # SIMULATE PAYMENT SUCCESS
        # (later: replace with real provider callback/webhook)
        # ===========================
        payment.status = "success"
        payment.save(update_fields=["status"])

        # ✅ Mark order paid
        order.status = "paid"
        order.save(update_fields=["status"])

        # ✅ Increase quantity_sold correctly
        ticket_type.quantity_sold += order.quantity
        ticket_type.save(update_fields=["quantity_sold"])

        # ✅ Create MULTIPLE tickets
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