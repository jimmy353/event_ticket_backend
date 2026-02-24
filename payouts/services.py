from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum

from payments.models import Payment
from payouts.models import Payout
from events.models import Event


def process_event_payouts():
    """
    Auto payout for events that already finished.
    Uses Payment model (real money source).
    Safe from duplication.
    """

    now = timezone.now()

    finished_events = Event.objects.filter(
        end_date__lt=now,
        payout_done=False
    )

    for event in finished_events:

        # Only collect successful & unpaid payments
        payments = Payment.objects.filter(
            order__event=event,
            status="success",
            payout_status="unpaid"
        )

        if not payments.exists():
            event.payout_done = True
            event.save()
            continue

        total_organizer_amount = payments.aggregate(
            total=Sum("organizer_amount")
        )["total"] or Decimal("0.00")

        if total_organizer_amount > 0:

            payout = Payout.objects.create(
                organizer=event.organizer,
                event=event,
                amount=total_organizer_amount,
                status="pending",
                note=f"Auto payout for event: {event.title}",
            )

            # Lock payments
            payments.update(payout_status="pending")

        event.payout_done = True
        event.save()