from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import OrganizerRequest

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "is_customer", "is_organizer", "is_staff", "is_active")
    list_filter = ("is_customer", "is_organizer", "is_staff", "is_active")
    search_fields = ("email",)


@admin.register(OrganizerRequest)
class OrganizerRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name", "momo_number", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email", "company_name")

    actions = ["approve_requests", "reject_requests"]

    def approve_requests(self, request, queryset):
        for req in queryset:
            req.status = "approved"
            req.save()

            user = req.user
            user.is_organizer = True
            user.is_customer = False
            user.save()

    approve_requests.short_description = "Approve selected organizer requests"

    def reject_requests(self, request, queryset):
        for req in queryset:
            req.status = "rejected"
            req.save()

    reject_requests.short_description = "Reject selected organizer requests"