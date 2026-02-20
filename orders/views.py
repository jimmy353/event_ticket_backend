from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Order
from tickets.models import TicketType, Ticket
from payments.models import Payment
from events.models import Event


# =====================================
# CREATE ORDER (USER)
# =====================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    ticket_id = request.data.get("ticket_id")
    quantity = int(request.data.get("quantity", 1))

    if not ticket_id:
        return Response({"error": "ticket_id required"}, status=400)

    if quantity < 1:
        return Response({"error": "quantity must be at least 1"}, status=400)

    try:
        ticket = TicketType.objects.select_related("event").get(id=ticket_id)
    except TicketType.DoesNotExist:
        return Response({"error": "Invalid ticket_id"}, status=404)

    available = ticket.quantity_total - ticket.quantity_sold
    if quantity > available:
        return Response({"error": f"Only {available} tickets remaining"}, status=400)

    total = ticket.price * Decimal(quantity)
    commission = total * Decimal("0.10")
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

    return Response({
        "id": order.id,
        "total_amount": float(order.total_amount),
        "commission_amount": float(order.commission_amount),
        "organizer_amount": float(order.organizer_amount),
        "status": order.status,
    }, status=201)


# =====================================
# USER ORDERS
# =====================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_orders(request):
    orders = (
        Order.objects
        .select_related("ticket_type", "ticket_type__event")
        .filter(user=request.user)
        .order_by("-created_at")
    )

    data = [{
        "id": o.id,
        "status": o.status,
        "quantity": o.quantity,
        "total_amount": float(o.total_amount),
        "created_at": o.created_at,
        "ticket_type_name": o.ticket_type.name,
        "event_title": o.ticket_type.event.title,
        "event_id": o.ticket_type.event.id,
    } for o in orders]

    return Response(data)


# =====================================
# REQUEST REFUND (USER)
# =====================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_refund(request, order_id):
    try:
        order = Order.objects.select_related(
            "ticket_type", "ticket_type__event"
        ).get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    if order.status != "paid":
        return Response({"error": "Only paid orders can request refund"}, status=400)

    event = order.ticket_type.event

    if event.start_date <= timezone.now():
        return Response({"error": "Event already started"}, status=400)

    used_ticket = Ticket.objects.filter(
        user=request.user,
        ticket_type=order.ticket_type,
        is_used=True
    ).exists()

    if used_ticket:
        return Response({"error": "Ticket already used"}, status=400)

    order.status = "refund_requested"
    order.save(update_fields=["status"])

    return Response({
        "message": "Refund request submitted",
        "order_id": order.id,
        "status": order.status
    })


# =====================================
# ORGANIZER REFUND REQUESTS
# =====================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_refund_requests(request):
    orders = (
        Order.objects
        .select_related("ticket_type__event", "user")
        .filter(
            ticket_type__event__organizer=request.user,
            status="refund_requested"
        )
        .order_by("-created_at")
    )

    data = [{
        "id": o.id,
        "quantity": o.quantity,
        "total_amount": float(o.total_amount),
        "customer_email": o.user.email,
        "ticket_type_name": o.ticket_type.name,
        "event_title": o.ticket_type.event.title,
        "created_at": o.created_at,
    } for o in orders]

    return Response(data)


# =====================================
# ORGANIZER APPROVE REFUND
# =====================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def organizer_approve_refund(request, order_id):

    try:
        order = Order.objects.select_related(
            "ticket_type__event", "user"
        ).get(id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    if order.ticket_type.event.organizer != request.user:
        return Response({"error": "Forbidden"}, status=403)

    if order.status != "refund_requested":
        return Response({"error": "Invalid refund state"}, status=400)

    if order.ticket_type.event.start_date <= timezone.now():
        return Response({"error": "Event already started"}, status=400)

    with transaction.atomic():

        payment = Payment.objects.filter(
            order=order,
            status="success"
        ).first()

        if payment:
            payment.status = "refunded"
            payment.save(update_fields=["status"])

        order.ticket_type.quantity_sold = max(
            order.ticket_type.quantity_sold - order.quantity, 0
        )
        order.ticket_type.save(update_fields=["quantity_sold"])

        Ticket.objects.filter(
            user=order.user,
            ticket_type=order.ticket_type
        ).order_by("-created_at")[:order.quantity].delete()

        order.status = "refunded"
        order.save(update_fields=["status"])

    return Response({
        "message": "Refund approved successfully",
        "order_id": order.id,
        "status": order.status
    })


# =====================================
# ORGANIZER ORDERS LIST
# =====================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_orders(request):

    orders = (
        Order.objects
        .select_related("ticket_type__event", "user")
        .filter(ticket_type__event__organizer=request.user)
        .order_by("-created_at")
    )

    data = [{
        "id": o.id,
        "status": o.status,
        "quantity": o.quantity,
        "total_amount": float(o.total_amount),
        "commission_amount": float(o.commission_amount),
        "organizer_amount": float(o.organizer_amount),
        "customer_email": o.user.email,
        "ticket_type_name": o.ticket_type.name,
        "event_title": o.ticket_type.event.title,
        "created_at": o.created_at,
    } for o in orders]

    return Response(data)


# =====================================
# ORGANIZER DASHBOARD ANALYTICS
# =====================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_dashboard_stats(request):

    paid_orders = Order.objects.filter(
        ticket_type__event__organizer=request.user,
        status="paid"
    )

    total_events = Event.objects.filter(
        organizer=request.user
    ).count()

    total_orders = paid_orders.count()

    total_revenue = paid_orders.aggregate(
        total=Sum("total_amount")
    )["total"] or Decimal("0")

    total_commission = paid_orders.aggregate(
        total=Sum("commission_amount")
    )["total"] or Decimal("0")

    total_organizer_earnings = paid_orders.aggregate(
        total=Sum("organizer_amount")
    )["total"] or Decimal("0")

    return Response({
        "total_events": total_events,
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "total_commission": float(total_commission),
        "total_organizer_earnings": float(total_organizer_earnings),
    })