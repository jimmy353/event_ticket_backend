from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from orders.models import Order


class Refund(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("processed", "Processed"),
        ("rejected", "Rejected"),
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="refund"
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    reason = models.TextField()

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    expected_refund_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def mark_processed(self):
        self.status = "processed"
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at"])

    def set_expected_refund_date(self):
        self.expected_refund_date = timezone.now().date() + timedelta(days=5)
        self.save(update_fields=["expected_refund_date"])

    def __str__(self):
        return f"Refund - Order #{self.order.id}"