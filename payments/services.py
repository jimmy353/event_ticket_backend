from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError

from orders.models import Order
from payments.models import Payment
from tickets.models import TicketType
from wallets.models import OrganizerWallet


COMMISSION_RATE = Decimal("0.10")


@transaction.atomic
def purchase_tickets(user, event, items):
    total_amount = Decimal("0.00")

    ticket_objects = []

    # 1️⃣ Validate availability
    for item in items:
        ticket = TicketType.objects.select_for_update().get(
            id=item["ticket_type_id"],
            event=event,
        )

        if ticket.quantity_sold + item["quantity"] > ticket.quantity_total:
            raise ValidationError(
                f"Not enough tickets for {ticket.name}"
            )

        subtotal = ticket.price * item["quantity"]
        total_amount += subtotal

        ticket_objects.append((ticket, item["quantity"], subtotal))

    # 2️⃣ Calculate commission
    commission_amount = total_amount * COMMISSION_RATE
    organizer_amount = total_amount - commission_amount

    # 3️⃣ Create order
    order = Order.objects.create(
        user=user,
        event=event,
        total_amount=total_amount,
        commission_amount=commission_amount,
        organizer_amount=organizer_amount,
        status=Order.STATUS_PENDING,
    )

    # 4️⃣ Create payments + update tickets
    for ticket, qty, subtotal in ticket_objects:
        Payment.objects.create(
            order=order,
            ticket_type=ticket,
            quantity=qty,
            amount=subtotal,
        )

        ticket.quantity_sold += qty
        ticket.save(update_fields=["quantity_sold"])

    # 5️⃣ Lock organizer funds
    wallet, _ = OrganizerWallet.objects.get_or_create(
        organizer=event.organizer
    )
    wallet.locked_balance += organizer_amount
    wallet.save(update_fields=["locked_balance"])

    return order
