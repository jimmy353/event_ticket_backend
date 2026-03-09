from django.db import models
from django.conf import settings
from django.utils import timezone


class Payment(models.Model):

    PROVIDERS = (
        ("momo", "MTN MoMo"),
        ("mgurush", "M-Gurush"),
    )

    STATUS = (
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    PAYOUT_STATUS = (
        ("unpaid", "Unpaid"),
        ("pending", "Pending Payout"),
        ("paid", "Paid Out"),
    )

    # ===============================
    # RELATIONS
    # ===============================
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payments"
    )

    # ===============================
    # PAYMENT INFO
    # ===============================
    provider = models.CharField(
        max_length=20,
        choices=PROVIDERS
    )

    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="pending"
    )

    # ===============================
    # FINANCE BREAKDOWN
    # ===============================
    commission = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    organizer_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    payout_status = models.CharField(
        max_length=20,
        choices=PAYOUT_STATUS,
        default="unpaid"
    )

    # ===============================
    # TIMESTAMPS
    # ===============================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ===============================
    # HELPERS
    # ===============================
    def mark_success(self):
        self.status = "success"
        self.save(update_fields=["status"])

    def mark_failed(self):
        self.status = "failed"
        self.save(update_fields=["status"])

    def mark_refunded(self):
        self.status = "refunded"
        self.save(update_fields=["status"])

    def __str__(self):
        return f"Payment #{self.id} - {self.provider} - {self.amount}"


# =====================================
# Saved Payment Method (Separate Model)
# =====================================
class SavedPaymentMethod(models.Model):

    PROVIDER_CHOICES = (
        ("MOMO", "MTN MoMo"),
        ("MGURUSH", "M-Gurush"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_payments"
    )

    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default="MOMO"
    )

    phone_number = models.CharField(max_length=20)

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.phone_number}"