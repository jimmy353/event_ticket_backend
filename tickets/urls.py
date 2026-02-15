from django.urls import path
from .views import (
    create_ticket,
    scan_ticket,
    list_ticket_types,
    create_ticket_type,
    update_ticket_type,
    delete_ticket_type,
    event_scan_stats,
)
from . import views

urlpatterns = [
    path("", list_ticket_types),  

    # Ticket Types (Organizer)
    path("type/create/", create_ticket_type),
    path("<int:ticket_type_id>/update/", update_ticket_type),
    path("<int:ticket_type_id>/delete/", delete_ticket_type),

    # Buy ticket
    path("create/", create_ticket),

    # Scan
    path("scan/", scan_ticket),

    # Organizer stats
    path("event/<int:event_id>/scan-stats/", event_scan_stats),

    # My tickets
    path("my/", views.my_tickets),
]