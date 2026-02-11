import uuid
from django.db import models
from django.conf import settings
from events.models import Event


class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ticket_types")
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_total = models.PositiveIntegerField(default=0)
    quantity_sold = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.event.title} - {self.name}"


class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tickets")
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name="tickets")

    ticket_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    qr_code = models.ImageField(upload_to="tickets/qr_codes/", null=True, blank=True)

    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    # ✅ NEW (REFUND SUPPORT)
    is_cancelled = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.ticket_type.event.title} - {self.ticket_type.name} ({self.ticket_code})"