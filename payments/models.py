from django.db import models


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
        ("pending", "Pending"),
        ("paid", "Paid"),
    )

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payments"
    )

    provider = models.CharField(max_length=20, choices=PROVIDERS)

    phone = models.CharField(max_length=20, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # 🔥 NEW FIELDS FOR FINANCE SYSTEM
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    organizer_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    payout_status = models.CharField(
        max_length=20,
        choices=PAYOUT_STATUS,
        default="unpaid"
    )

    status = models.CharField(max_length=20, choices=STATUS, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider} - {self.amount}"