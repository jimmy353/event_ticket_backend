from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


def generate_payout_reference():
    return f"PAYOUT-{uuid.uuid4().hex[:10].upper()}"


class Payout(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending Approval"),
        ("processing", "Processing"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    )

    # ===============================
    # UNIQUE REFERENCE
    # ===============================
    reference = models.CharField(
        max_length=40,
        unique=True,
        editable=False,
        null=True,
        blank=True
    )

    # ===============================
    # RELATIONS
    # ===============================
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payouts"
    )

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="payouts",
        null=True,
        blank=True,
    )

    # ===============================
    # FINANCIAL DATA
    # ===============================
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    # ===============================
    # PAYMENT PROVIDER TRACKING
    # ===============================
    provider_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    failure_reason = models.TextField(
        blank=True,
        null=True
    )

    note = models.TextField(
        blank=True,
        null=True
    )

    # ===============================
    # TIMESTAMPS
    # ===============================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    # ===============================
    # HELPERS
    # ===============================
    def mark_processing(self):
        self.status = "processing"
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at"])

    def mark_paid(self):
        self.status = "paid"
        self.paid_at = timezone.now()
        self.save(update_fields=["status", "paid_at"])

    def mark_failed(self, reason=None):
        self.status = "failed"
        self.failure_reason = reason
        self.save(update_fields=["status", "failure_reason"])

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_payout_reference()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} - {self.organizer.email} - {self.amount}"