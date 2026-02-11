from decimal import Decimal
from django.core.management.base import BaseCommand
from payments.models import Payment
from wallets.models import OrganizerWallet, PlatformWallet, Payout


class Command(BaseCommand):
    help = "Fix wallet balances from existing successful payments"

    def handle(self, *args, **kwargs):
        platform_wallet, _ = PlatformWallet.objects.get_or_create(id=1)

        success_payments = Payment.objects.filter(status="success")

        count = 0

        for payment in success_payments:
            order = payment.order

            # skip already paid orders
            if order.status == "paid":
                continue

            order.status = "paid"
            order.save()

            organizer = order.ticket_type.event.organizer
            organizer_wallet, _ = OrganizerWallet.objects.get_or_create(organizer=organizer)

            platform_wallet.balance += Decimal(order.commission_amount)
            organizer_wallet.balance += Decimal(order.organizer_amount)

            organizer_wallet.save()

            Payout.objects.create(
                organizer=organizer,
                order=order,
                amount=order.organizer_amount,
                status="pending"
            )

            count += 1

        platform_wallet.save()

        self.stdout.write(self.style.SUCCESS(f"✅ Wallets fixed. Updated {count} orders."))