from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum

from events.models import Event
from orders.models import Order


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organizer_dashboard(request):
    user = request.user

    total_events = Event.objects.filter(organizer=user).count()

    paid_orders = Order.objects.filter(
        ticket_type__event__organizer=user,
        status="paid"
    )

    total_orders = paid_orders.count()

    total_sales = paid_orders.aggregate(total=Sum("total_amount"))["total"] or 0

    organizer_balance = paid_orders.aggregate(total=Sum("organizer_amount"))["total"] or 0

    pending_payouts = Order.objects.filter(
        ticket_type__event__organizer=user,
        status="paid",
        payout__isnull=True
    ).aggregate(total=Sum("organizer_amount"))["total"] or 0

    paid_payouts = Order.objects.filter(
        ticket_type__event__organizer=user,
        status="paid",
        payout__isnull=False
    ).aggregate(total=Sum("organizer_amount"))["total"] or 0

    return Response({
        "total_events": total_events,
        "total_orders": total_orders,
        "total_sales": total_sales,
        "organizer_balance": organizer_balance,
        "pending_payouts": pending_payouts,
        "paid_payouts": paid_payouts,
    })