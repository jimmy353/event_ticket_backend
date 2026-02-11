from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal

from events.models import Event
from wallets.models import OrganizerWallet
from payouts.models import Payout


class Command(BaseCommand):
    help = "Automatically pay organizers after event ends"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        ended_events = Event.objects.filter(end_date__lt=now)

        total_paid = 0
        total_skipped = 0

        for event in ended_events:
            organizer = event.organizer

            try:
                wallet = OrganizerWallet.objects.get(organizer=organizer)

                if wallet.balance <= 0:
                    total_skipped += 1
                    continue

                amount_to_pay = wallet.balance

                # Create payout record
                Payout.objects.create(
                    organizer=organizer,
                    amount=amount_to_pay,
                    status="paid",
                    paid_at=timezone.now(),
                    note=f"Auto payout after event ended: {event.title}"
                )

                # Reset wallet balance
                wallet.balance = Decimal("0.00")
                wallet.save()

                total_paid += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Paid organizer {organizer.email} SSP {amount_to_pay} for event {event.title}"
                ))

            except OrganizerWallet.DoesNotExist:
                total_skipped += 1
                self.stdout.write(self.style.WARNING(
                    f"Skipped organizer {organizer.email} (no wallet found)"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Auto payouts complete. Paid: {total_paid}, Skipped: {total_skipped}"
        ))
