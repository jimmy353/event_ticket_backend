from django.core.management.base import BaseCommand
from payouts.services import process_event_payouts


class Command(BaseCommand):
    help = "Process automatic payouts for finished events"

    def handle(self, *args, **kwargs):
        process_event_payouts()
        self.stdout.write(self.style.SUCCESS("✅ Payout processing complete"))
