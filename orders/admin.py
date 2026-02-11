from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "get_event",
        "ticket_type",
        "quantity",
        "total_amount",
        "commission_amount",
        "organizer_amount",
        "status",
        "created_at",
    )

    list_filter = ("status", "created_at")
    search_fields = ("id", "user__email")

    def get_event(self, obj):
        return obj.ticket_type.event

    get_event.short_description = "Event"