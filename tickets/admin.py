from django.contrib import admin
from django.utils.html import format_html
from .models import TicketType, Ticket


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "name", "price", "quantity_total", "quantity_sold")
    search_fields = ("name", "event__title")
    list_filter = ("event",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "ticket_type", "ticket_code", "is_used", "created_at")
    list_filter = ("is_used", "created_at")
    search_fields = ("ticket_code", "user__email", "ticket_type__name", "ticket_type__event__title")

    readonly_fields = ("ticket_code", "qr_preview", "created_at")

    def qr_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="150" height="150" />', obj.qr_code.url)
        return "No QR Code"

    qr_preview.short_description = "QR Code"