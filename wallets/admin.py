from django.contrib import admin
from .models import PlatformWallet, OrganizerWallet, Payout


@admin.register(PlatformWallet)
class PlatformWalletAdmin(admin.ModelAdmin):
    list_display = ("id", "balance", "updated_at")


@admin.register(OrganizerWallet)
class OrganizerWalletAdmin(admin.ModelAdmin):
    list_display = ("id", "organizer", "balance", "updated_at")
    search_fields = ("organizer__email",)


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ("id", "organizer", "order", "amount", "status", "created_at", "paid_at")
    search_fields = ("organizer__email",)
    list_filter = ("status",)
