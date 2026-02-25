from django.contrib import admin
from .models import Refund


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("reference", "order", "status", "amount", "requested_at", "approved_at", "paid_at")
    search_fields = ("reference", "order__id", "order__user__email")
    list_filter = ("status", "provider")