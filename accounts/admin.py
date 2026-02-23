from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import OrganizerRequest, EmailOTP

User = get_user_model()


class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "is_organizer", "is_verified", "is_staff"]
    search_fields = ["email"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "is_organizer",
                "is_verified",
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "password1",
                "password2",
                "is_staff",
                "is_superuser",
            ),
        }),
    )


admin.site.register(User, UserAdmin)
admin.site.register(OrganizerRequest)
admin.site.register(EmailOTP)