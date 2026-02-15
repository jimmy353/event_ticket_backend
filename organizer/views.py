from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from events.models import Event
from orders.models import Order
from django.db.models import Sum


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_dashboard(request):
    user = request.user

    total_events = Event.objects.filter(organizer=user).count()

    total_orders = Order.objects.filter(
        ticket_type__event__organizer=user,
        status="paid"
    ).count()

    total_sales = Order.objects.filter(
        ticket_type__event__organizer=user,
        status="paid"
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    organizer_balance = Order.objects.filter(
        ticket_type__event__organizer=user,
        status="paid"
    ).aggregate(total=Sum("organizer_amount"))["total"] or 0

    pending_payouts = 0
    paid_payouts = 0

    return Response({
        "total_events": total_events,
        "total_orders": total_orders,
        "total_sales": total_sales,
        "organizer_balance": organizer_balance,
        "pending_payouts": pending_payouts,
        "paid_payouts": paid_payouts,
    })