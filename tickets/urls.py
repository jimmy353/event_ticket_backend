from django.urls import path
from .views import (
    create_ticket,
    scan_ticket,
    list_ticket_types,
    create_ticket_type,
    update_ticket_type,
    delete_ticket_type,
)
from . import views

urlpatterns = [
    path("", list_ticket_types),                      # GET /api/tickets/?event=1
    path("type/create/", create_ticket_type),         # POST /api/tickets/type/create/
    path("type/<int:ticket_type_id>/update/", update_ticket_type),  # PUT/PATCH
    path("type/<int:ticket_type_id>/delete/", delete_ticket_type),  # DELETE

    path("create/", create_ticket),                   # POST /api/tickets/create/
    path("scan/", scan_ticket),                       # POST /api/tickets/scan/
    path("my/", views.my_tickets),                    # GET /api/tickets/my/
]