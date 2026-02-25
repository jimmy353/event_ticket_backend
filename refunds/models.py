import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone


def generate_refund_reference():
    return f"REF-{uuid.uuid4().hex[:10].upper()}"


class Refund(models.Model):

    STATUS_CHOICES = (
        ("requested", "Requested"),
        ("approved", "Approved"),
        ("processing", "Processing"),
        ("paid", "Paid"),
        ("rejected", "Rejected"),
    )

    reference = models.CharField(
        max_length=40,
        unique=True,
        editable=False,
        blank=True,
        null=True
    )

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="refund",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="requested"
    )

    reason = models.TextField(blank=True, null=True)
    admin_note = models.TextField(blank=True, null=True)

    provider = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )  # MOMO / MGURUSH

    provider_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)

    # 3–7 days settlement estimate
    expected_paid_from = models.DateTimeField(blank=True, null=True)
    expected_paid_to = models.DateTimeField(blank=True, null=True)

    paid_at = models.DateTimeField(blank=True, null=True)

    # =========================================
    # SAVE OVERRIDE (AUTO SYNC ORDER STATUS)
    # =========================================
    def save(self, *args, **kwargs):

        if not self.reference:
            self.reference = generate_refund_reference()

        super().save(*args, **kwargs)

        # 🔥 Auto-sync Order when refund fully paid
        if self.status == "paid":
            if self.order.status != "refunded":
                self.order.status = "refunded"
                self.order.save(update_fields=["status"])

    # =========================================
    # HELPERS
    # =========================================
    def mark_processing(self):
        self.status = "processing"
        now = timezone.now()
        self.expected_paid_from = now + timedelta(days=3)
        self.expected_paid_to = now + timedelta(days=7)
        self.save(update_fields=[
            "status",
            "expected_paid_from",
            "expected_paid_to"
        ])

    def mark_paid(self, provider_reference=None):
        self.status = "paid"
        self.paid_at = timezone.now()

        if provider_reference:
            self.provider_reference = provider_reference

        self.save(update_fields=[
            "status",
            "paid_at",
            "provider_reference"
        ])

    def __str__(self):
        return f"{self.reference} - Order #{self.order_id} - {self.status}"