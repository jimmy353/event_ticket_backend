from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Order
from tickets.models import TicketType, Ticket
from payments.models import Payment


# ===============================
# CREATE ORDER (USER)
# ===============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    ticket_id = request.data.get("ticket_id")
    quantity = int(request.data.get("quantity", 1))

    if not ticket_id:
        return Response(
            {"error": "ticket_id required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if quantity < 1:
        return Response(
            {"error": "quantity must be at least 1"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        ticket = TicketType.objects.select_related("event").get(id=ticket_id)
    except TicketType.DoesNotExist:
        return Response(
            {"error": "Invalid ticket_id"},
            status=status.HTTP_404_NOT_FOUND
        )

    # ✅ Check availability
    available = ticket.quantity_total - ticket.quantity_sold
    if quantity > available:
        return Response(
            {"error": f"Only {available} tickets remaining"},
            status=status.HTTP_400_BAD_REQUEST
        )

    total = ticket.price * Decimal(quantity)
    commission = total * Decimal("0.10")  # 10%
    organizer_amount = total - commission

    order = Order.objects.create(
        user=request.user,
        ticket_type=ticket,
        quantity=quantity,
        total_amount=total,
        commission_amount=commission,
        organizer_amount=organizer_amount,
        status="pending"
    )

    return Response(
        {
            "id": order.id,
            "total_amount": float(order.total_amount),
            "commission_amount": float(order.commission_amount),
            "organizer_amount": float(order.organizer_amount),
            "status": order.status,
        },
        status=status.HTTP_201_CREATED
    )


# ===============================
# MY ORDERS (USER)
# ===============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_orders(request):
    orders = (
        Order.objects
        .select_related("ticket_type", "ticket_type__event")
        .filter(user=request.user)
        .order_by("-created_at")
    )

    data = []
    for o in orders:
        data.append({
            "id": o.id,
            "status": o.status,
            "quantity": o.quantity,
            "total_amount": float(o.total_amount),
            "created_at": o.created_at,
            "ticket_type_name": o.ticket_type.name,
            "event_title": o.ticket_type.event.title,
            "event_id": o.ticket_type.event.id,
        })

    return Response(data, status=status.HTTP_200_OK)


# ===============================
# REQUEST REFUND (USER)
# ===============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_refund(request, order_id):
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

    event = order.ticket_type.event

    # ❌ Block refund if event started
    if event.start_date <= timezone.now():
        return Response(
            {"error": "Refund not allowed. Event already started."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ❌ Block refund if any ticket already scanned
    used_ticket_exists = Ticket.objects.filter(
        user=request.user,
        ticket_type=order.ticket_type,
        is_used=True
    ).exists()

    if used_ticket_exists:
        return Response(
            {"error": "Refund not allowed. Ticket already used."},
            status=status.HTTP_400_BAD_REQUEST
        )

    order.status = "refund_requested"
    order.save(update_fields=["status"])

    return Response(
        {
            "message": "Refund request submitted successfully",
            "order_id": order.id,
            "status": order.status,
        },
        status=status.HTTP_200_OK
    )


# ===============================
# ORGANIZER REFUND LIST
# ===============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_refund_requests(request):
    orders = (
        Order.objects
        .select_related("ticket_type", "ticket_type__event", "user")
        .filter(ticket_type__event__organizer=request.user, status="refund_requested")
        .order_by("-created_at")
    )

    data = []
    for o in orders:
        data.append({
            "id": o.id,
            "status": o.status,
            "quantity": o.quantity,
            "total_amount": float(o.total_amount),
            "created_at": o.created_at,
            "customer_email": o.user.email,
            "ticket_type_name": o.ticket_type.name,
            "event_title": o.ticket_type.event.title,
        })

    return Response(data, status=status.HTTP_200_OK)


# ===============================
# ORGANIZER APPROVE REFUND
# ===============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def organizer_approve_refund(request, order_id):
    try:
        order = Order.objects.select_related(
            "ticket_type",
            "ticket_type__event",
            "user"
        ).get(id=order_id)
    except Order.DoesNotExist:
        return Response(
            {"error": "Order not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    event = order.ticket_type.event

    # 🔐 Only event organizer
    if event.organizer != request.user:
        return Response(
            {"error": "You are not allowed"},
            status=status.HTTP_403_FORBIDDEN
        )

    if order.status != "refund_requested":
        return Response(
            {"error": "Refund not requested for this order"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if event.start_date <= timezone.now():
        return Response(
            {"error": "Refund not allowed. Event already started."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ✅ Refund process atomic
    with transaction.atomic():
        # update payment
        payment = Payment.objects.filter(order=order, status="success").first()
        if payment:
            payment.status = "refunded"
            payment.save(update_fields=["status"])

        # return stock
        order.ticket_type.quantity_sold = max(
            order.ticket_type.quantity_sold - order.quantity,
            0
        )
        order.ticket_type.save(update_fields=["quantity_sold"])

        # cancel tickets (delete tickets)
        Ticket.objects.filter(
            user=order.user,
            ticket_type=order.ticket_type
        ).order_by("-created_at")[:order.quantity].delete()

        # update order
        order.status = "refunded"
        order.save(update_fields=["status"])

    return Response(
        {
            "message": "Refund approved and processed successfully",
            "order_id": order.id,
            "status": order.status,
        },
        status=status.HTTP_200_OK
    )


# ===============================
# ORGANIZER ORDERS LIST
# ===============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_orders(request):
    orders = (
        Order.objects
        .select_related("ticket_type", "ticket_type__event", "user")
        .filter(ticket_type__event__organizer=request.user)
        .order_by("-created_at")
    )

    data = []
    for o in orders:
        data.append({
            "id": o.id,
            "status": o.status,
            "quantity": o.quantity,
            "total_amount": float(o.total_amount),
            "commission_amount": float(o.commission_amount),
            "organizer_amount": float(o.organizer_amount),
            "created_at": o.created_at,
            "customer_email": o.user.email,
            "ticket_type_name": o.ticket_type.name,
            "event_title": o.ticket_type.event.title,
        })

    return Response(data, status=status.HTTP_200_OK)