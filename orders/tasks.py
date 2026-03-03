from django.utils import timezone
from datetime import timedelta
from accounts.models import PushToken, PushLog
from .models import Order
from utils.push import send_expo_push


def send_event_reminders():
    now = timezone.now()

    orders = (
        Order.objects
        .filter(
            status="paid",
            ticket_type__event__start_date__gt=now
        )
        .select_related("ticket_type__event", "user")
    )

    for order in orders:
        event = order.ticket_type.event

        if not event or not event.start_date:
            continue

        event_time = event.start_date

        # Ensure timezone-aware comparison
        if timezone.is_naive(event_time):
            event_time = timezone.make_aware(event_time)

        time_left = event_time - now

        # 24 hour reminder window
        if timedelta(hours=23, minutes=50) < time_left <= timedelta(hours=24):
            send_reminder(order, event, "24h")

        # 1 hour reminder window
        elif timedelta(minutes=50) < time_left <= timedelta(hours=1):
            send_reminder(order, event, "1h")