from django.core.management.base import BaseCommand
from utils.event_reminders import send_event_reminders


class Command(BaseCommand):
    help = "Send event reminder notifications"

    def handle(self, *args, **kwargs):

        send_event_reminders()

        self.stdout.write(self.style.SUCCESS("Event reminders sent successfully"))