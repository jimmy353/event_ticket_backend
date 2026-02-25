from django.contrib import admin
from .models import Refund


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "amount", "expected_refund_date")
    list_filter = ("status",)