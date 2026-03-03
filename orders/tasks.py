from django.utils import timezone
from datetime import timedelta
from accounts.models import PushToken, PushLog
from .models import Order
from utils.push import send_expo_push


def send_event_reminders():
    now = timezone.now()

    orders = (
        Order.objects
        .filter(status="paid")
        .select_related("ticket_type__event", "user")
    )

    for order in orders:
        event = order.ticket_type.event
        event_time = event.start_date
        time_left = event_time - now

        # 24 hours
        if timedelta(hours=23, minutes=50) < time_left <= timedelta(hours=24):
            send_reminder(order, event, "24h")

        # 1 hour
        if timedelta(minutes=50) < time_left <= timedelta(hours=1):
            send_reminder(order, event, "1h")


def send_reminder(order, event, reminder_type):

    already_sent = PushLog.objects.filter(
        user=order.user,
        event=event,
        reminder_type=reminder_type
    ).exists()

    if already_sent:
        return

    tokens = PushToken.objects.filter(
        user=order.user
    ).values_list("token", flat=True)

    if not tokens:
        return

    if reminder_type == "24h":
        body = f"{event.title} starts in 24 hours!"
    else:
        body = f"{event.title} starts in 1 hour!"

    send_expo_push(tokens, "Event Reminder 🔔", body)

    PushLog.objects.create(
        user=order.user,
        event=event,
        reminder_type=reminder_type
    )