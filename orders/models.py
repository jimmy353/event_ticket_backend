from django.db import models
from django.conf import settings


class Order(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("refund_requested", "Refund Requested"),
        ("refunded", "Refunded"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    ticket_type = models.ForeignKey(
        "tickets.TicketType",
        on_delete=models.CASCADE,
        related_name="orders"
    )

    quantity = models.PositiveIntegerField(default=1)

    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    organizer_amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id}"