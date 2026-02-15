from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import Ticket, TicketType
from .serializers import TicketTypeSerializer
from events.models import Event


# ===============================
# TICKET TYPES
# ===============================

@api_view(["GET"])
def list_ticket_types(request):
    event_id = request.GET.get("event")

    if not event_id:
        return Response(
            {"error": "event parameter is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response(
            {"error": "Event not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    ticket_types = TicketType.objects.filter(event=event)

    data = [
        {
            "id": t.id,
            "name": t.name,
            "price": str(t.price),
            "quantity_total": t.quantity_total,
            "quantity_sold": t.quantity_sold,
            "available": max(t.quantity_total - t.quantity_sold, 0),
        }
        for t in ticket_types
    ]

    return Response(data, status=status.HTTP_200_OK)


# ===============================
# CREATE TICKET TYPE (ORGANIZER)
# ===============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_ticket_type(request):
    serializer = TicketTypeSerializer(data=request.data)

    if serializer.is_valid():
        ticket_type = serializer.save()

        # 🔐 Only organizer can create ticket type for their own event
        if ticket_type.event.organizer != request.user:
            ticket_type.delete()
            return Response(
                {"error": "You can only create ticket types for your own events"},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# UPDATE TICKET TYPE (ORGANIZER)
# ===============================

@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_ticket_type(request, ticket_type_id):
    try:
        ticket_type = TicketType.objects.select_related("event").get(id=ticket_type_id)
    except TicketType.DoesNotExist:
        return Response({"error": "Ticket type not found"}, status=status.HTTP_404_NOT_FOUND)

    # 🔐 Only event organizer can update
    if ticket_type.event.organizer != request.user:
        return Response({"error": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

    serializer = TicketTypeSerializer(ticket_type, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# DELETE TICKET TYPE (ORGANIZER)
# ===============================

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_ticket_type(request, ticket_type_id):
    try:
        ticket_type = TicketType.objects.select_related("event").get(id=ticket_type_id)
    except TicketType.DoesNotExist:
        return Response({"error": "Ticket type not found"}, status=status.HTTP_404_NOT_FOUND)

    # 🔐 Only organizer can delete
    if ticket_type.event.organizer != request.user:
        return Response({"error": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

    ticket_type.delete()
    return Response({"message": "Ticket type deleted successfully"}, status=status.HTTP_200_OK)


# ===============================
# BUY / CREATE TICKET (USER)
# ===============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_ticket(request):
    ticket_type_id = request.data.get("ticket_type_id")
    quantity = request.data.get("quantity", 1)

    try:
        quantity = int(quantity)
        if quantity < 1:
            raise ValueError
    except:
        return Response(
            {"error": "quantity must be a valid number >= 1"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not ticket_type_id:
        return Response(
            {"error": "ticket_type_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        ticket_type = TicketType.objects.get(id=ticket_type_id)
    except TicketType.DoesNotExist:
        return Response(
            {"error": "Ticket type not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    available = ticket_type.quantity_total - ticket_type.quantity_sold

    if quantity > available:
        return Response(
            {"error": f"Only {available} tickets remaining"},
            status=status.HTTP_400_BAD_REQUEST
        )

    created_tickets = []

    for _ in range(quantity):
        ticket = Ticket.objects.create(
            user=request.user,
            ticket_type=ticket_type
        )

        created_tickets.append({
            "id": str(ticket.id),
            "ticket_code": str(ticket.ticket_code),
        })

    ticket_type.quantity_sold += quantity
    ticket_type.save(update_fields=["quantity_sold"])

    return Response(
        {
            "message": "Tickets created successfully",
            "event": ticket_type.event.title,
            "ticket_type": ticket_type.name,
            "user_email": request.user.email,
            "quantity": quantity,
            "tickets": created_tickets,
        },
        status=status.HTTP_201_CREATED
    )


# ===============================
# SCAN TICKET (ORGANIZER ONLY)
# ===============================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def scan_ticket(request):
    ticket_code = request.data.get("ticket_code")
    event_id = request.data.get("event_id")

    if not ticket_code or not event_id:
        return Response(
            {"error": "ticket_code and event_id are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        ticket = Ticket.objects.select_related(
            "ticket_type",
            "ticket_type__event",
            "user"
        ).get(ticket_code=ticket_code)
    except Ticket.DoesNotExist:
        return Response(
            {"error": "Invalid ticket"},
            status=status.HTTP_404_NOT_FOUND
        )

    event = ticket.ticket_type.event

    if event.organizer != request.user:
        return Response(
            {"error": "You are not allowed to scan tickets for this event"},
            status=status.HTTP_403_FORBIDDEN
        )

    if str(event.id) != str(event_id):
        return Response(
            {"error": "Ticket does not belong to this event"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if ticket.is_cancelled:
        return Response(
            {"error": "Ticket refunded/cancelled"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if ticket.is_used:
        return Response(
            {"error": "Ticket already used"},
            status=status.HTTP_400_BAD_REQUEST
        )

    ticket.is_used = True
    ticket.used_at = timezone.now()
    ticket.save(update_fields=["is_used", "used_at"])

    return Response(
        {
            "message": "Ticket scanned successfully",
            "ticket": {
                "ticket_code": str(ticket.ticket_code),
                "user_email": ticket.user.email,
                "event": event.title,
                "ticket_type": ticket.ticket_type.name,
                "used_at": ticket.used_at,
            }
        },
        status=status.HTTP_200_OK
    )


# ===============================
# MY TICKETS
# ===============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_tickets(request):
    tickets = (
        Ticket.objects
        .select_related("ticket_type", "ticket_type__event")
        .filter(user=request.user)
        .order_by("-created_at")
    )

    data = [
        {
            "id": str(t.id),
            "ticket_code": str(t.ticket_code),
            "ticket_name": t.ticket_type.name,
            "price": str(t.ticket_type.price),
            "is_used": t.is_used,
            "event_title": t.ticket_type.event.title,
            "event_date": (
                t.ticket_type.event.start_date.isoformat()
                if t.ticket_type.event.start_date
                else None
            ),
            "location": getattr(t.ticket_type.event, "location", "Unknown"),
            "seat": "A12",
            "order_id": f"ORD-{str(t.id)[:6]}",
        }
        for t in tickets
    ]

    return Response(data, status=status.HTTP_200_OK)