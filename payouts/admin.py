from django.contrib import admin
from django.utils import timezone
from .models import Payout


@admin.action(description="Mark selected payouts as PAID")
def mark_as_paid(modeladmin, request, queryset):
    queryset.update(status="paid", paid_at=timezone.now())


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ("id", "organizer", "amount", "status", "created_at", "paid_at")
    list_filter = ("status", "created_at")
    search_fields = ("organizer__email",)
    actions = [mark_as_paid]
