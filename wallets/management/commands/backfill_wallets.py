from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from payments.models import Payment
from wallets.models import PlatformWallet, OrganizerWallet, Payout


class Command(BaseCommand):
    help = "Backfill wallets and payouts from existing successful payments."

    def handle(self, *args, **kwargs):

        success_payments = Payment.objects.filter(status="success")

        if not success_payments.exists():
            self.stdout.write(self.style.WARNING("No successful payments found."))
            return

        platform_wallet, _ = PlatformWallet.objects.get_or_create(
            id=1,
            defaults={"balance": Decimal("0.00")}
        )

        count = 0

        for payment in success_payments:
            order = payment.order

            # skip if payout already created
            if Payout.objects.filter(order=order).exists():
                continue

            organizer = order.ticket_type.event.organizer
            commission = Decimal(order.commission_amount)
            organizer_amount = Decimal(order.organizer_amount)

            with transaction.atomic():

                order.status = "paid"
                order.save(update_fields=["status"])

                PlatformWallet.objects.filter(id=platform_wallet.id).update(
                    balance=F("balance") + commission
                )

                organizer_wallet, _ = OrganizerWallet.objects.get_or_create(
                    organizer=organizer,
                    defaults={"balance": Decimal("0.00")}
                )

                OrganizerWallet.objects.filter(id=organizer_wallet.id).update(
                    balance=F("balance") + organizer_amount
                )

                Payout.objects.create(
                    organizer=organizer,
                    order=order,
                    amount=organizer_amount,
                    status="pending"
                )

                count += 1

        self.stdout.write(self.style.SUCCESS(f"Backfilled {count} payouts + wallet credits successfully."))
