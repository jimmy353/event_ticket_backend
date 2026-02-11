from decimal import Decimal
from django.utils import timezone
from orders.models import Order
from payouts.models import Payout
from events.models import Event


def process_event_payouts():
    """
    Auto payout for events that already finished.
    Runs safely (won't duplicate payouts).
    """

    now = timezone.now()

    finished_events = Event.objects.filter(end_date__lt=now, payout_done=False)

    for event in finished_events:
        paid_orders = Order.objects.filter(event=event, status="paid")

        total_organizer_amount = Decimal("0.00")

        for order in paid_orders:
            total_organizer_amount += order.organizer_amount

        if total_organizer_amount > 0:
            Payout.objects.create(
                organizer=event.organizer,
                amount=total_organizer_amount,
                status="pending",
                note=f"Auto payout for event: {event.title}",
            )

        event.payout_done = True
        event.save()
