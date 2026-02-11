from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F

from payments.models import Payment
from wallets.models import PlatformWallet, OrganizerWallet, Payout


@receiver(post_save, sender=Payment)
def credit_wallets_after_success_payment(sender, instance, created, **kwargs):
    """
    When payment becomes SUCCESS:
    - Mark order as PAID
    - Add commission to PlatformWallet
    - Add organizer money to OrganizerWallet
    - Create payout record
    """

    if instance.status != "success":
        return

    order = instance.order

    # Avoid double crediting if payment is saved again
    payout_exists = Payout.objects.filter(order=order).exists()
    if payout_exists:
        return

    # Organizer is the event organizer from ticket_type.event.organizer
    organizer = order.ticket_type.event.organizer

    commission = Decimal(order.commission_amount)
    organizer_amount = Decimal(order.organizer_amount)

    with transaction.atomic():

        # Mark order paid
        order.status = "paid"
        order.save(update_fields=["status"])

        # Platform wallet (single row)
        platform_wallet, _ = PlatformWallet.objects.get_or_create(
            id=1,
            defaults={"balance": Decimal("0.00")}
        )
        PlatformWallet.objects.filter(id=platform_wallet.id).update(
            balance=F("balance") + commission
        )

        # Organizer wallet
        organizer_wallet, _ = OrganizerWallet.objects.get_or_create(
            organizer=organizer,
            defaults={"balance": Decimal("0.00")}
        )
        OrganizerWallet.objects.filter(id=organizer_wallet.id).update(
            balance=F("balance") + organizer_amount
        )

        # Create payout record
        Payout.objects.create(
            organizer=organizer,
            order=order,
            amount=organizer_amount,
            status="pending"
        )
