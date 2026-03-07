from django.urls import path
from .views import (
    request_refund,
    organizer_refunds,
    admin_approve_refund,
    admin_mark_refund_paid,
    my_refunds,
)

urlpatterns = [
    path("request/", request_refund),
    path("organizer/", organizer_refunds),
    path("admin/<int:refund_id>/approve/", admin_approve_refund),
    path("admin/<int:refund_id>/mark-paid/", admin_mark_refund_paid),
    path("my/", my_refunds),
]