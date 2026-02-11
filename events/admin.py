from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "location",
        "start_date",
        "end_date",
    )

    list_filter = ("category",)
    search_fields = ("title", "location")
    ordering = ("start_date",)
