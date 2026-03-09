from django.utils import timezone
from datetime import timedelta

from events.models import Event
from orders.models import Order
from accounts.models import PushToken, PushLog
from utils.push import send_expo_push


def send_event_reminders():

    now = timezone.now()
    reminder_time = now + timedelta(hours=24)

    events = Event.objects.filter(start_date__range=(now, reminder_time))

    for event in events:

        orders = Order.objects.filter(event=event, status="paid")

        for order in orders:

            user = order.user

            # avoid duplicate reminders
            if PushLog.objects.filter(
                user=user,
                event=event,
                reminder_type="24h"
            ).exists():
                continue

            tokens = PushToken.objects.filter(user=user).values_list("token", flat=True)

            if tokens:

                send_expo_push(
                    tokens,
                    "Event Reminder ⏰",
                    f"{event.title} starts in 24 hours. Don't miss it!"
                )

                PushLog.objects.create(
                    user=user,
                    event=event,
                    reminder_type="24h"
                )