from django.conf import settings
from payouts.services import process_event_payouts


def run_auto_payout():
    if getattr(settings, "AUTO_PAYOUT_ON_STARTUP", False):
        try:
            process_event_payouts()
        except Exception as e:
            print("AUTO PAYOUT ERROR:", e)
