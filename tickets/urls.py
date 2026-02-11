from django.urls import path
from .views import (
    create_ticket,
    scan_ticket,
    list_ticket_types,
    create_ticket_type,
    event_scan_stats,
)
from . import views

urlpatterns = [
    path("", list_ticket_types),                    # GET
    path("type/create/", create_ticket_type),       # POST (organizer)
    path("create/", create_ticket),                 # POST (buy ticket)
    path("scan/", scan_ticket),                     # POST (scan QR)
    path("event/<int:event_id>/scan-stats/", event_scan_stats),  # ✅ NEW
    path("my/", views.my_tickets),
]