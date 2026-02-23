from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import OrganizerRequest, EmailOTP

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = [
        "email",
        "is_customer",
        "is_organizer",
        "is_verified",
        "is_staff",
        "is_active",
    ]
    list_filter = ["is_customer", "is_organizer", "is_verified", "is_staff", "is_active"]
    search_fields = ["email", "full_name", "phone"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "phone")}),
        ("Roles", {"fields": ("is_customer", "is_organizer")}),
        ("Verification", {"fields": ("is_verified",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_customer", "is_organizer", "is_staff", "is_superuser"),
        }),
    )

    filter_horizontal = ("groups", "user_permissions")


@admin.register(OrganizerRequest)
class OrganizerRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name", "momo_number", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__email", "company_name", "momo_number")


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("email", "purpose", "otp_code", "is_used", "created_at", "expires_at")
    list_filter = ("purpose", "is_used", "created_at")
    search_fields = ("email", "otp_code")