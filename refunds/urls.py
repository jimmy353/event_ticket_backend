from django.urls import path
from .views import (
    request_refund,
    organizer_refunds,
    admin_approve_refund,
)

urlpatterns = [
    path("request/", request_refund),
    path("organizer/", organizer_refunds),
    path("admin/<int:refund_id>/approve/", admin_approve_refund),
]