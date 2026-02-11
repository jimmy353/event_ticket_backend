from django.db import transaction
from django.utils import timezone

from .models import Order
from wallets.models import OrganizerWallet


@transaction.atomic
def release_organizer_payout(order: Order):
    if order.status != Order.STATUS_PAID:
        raise ValueError("Order is not paid.")

    if order.payout_released:
        raise ValueError("Payout already released.")

    if order.event.end_date > timezone.now():
        raise ValueError("Event has not ended yet.")

    organizer_wallet = OrganizerWallet.objects.select_for_update().get(
        owner=order.event.organizer
    )

    if organizer_wallet.locked_balance < order.organizer_amount:
        raise ValueError("Insufficient locked balance.")

    organizer_wallet.locked_balance -= order.organizer_amount
    organizer_wallet.balance += order.organizer_amount
    organizer_wallet.save()

    order.payout_released = True
    order.save()