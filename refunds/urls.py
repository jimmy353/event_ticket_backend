from django.urls import path
from .views import (
    create_refund_request,
    organizer_refund_requests,
    approve_refund,
    reject_refund,
)

urlpatterns = [
    path("request/", create_refund_request),                 # USER
    path("organizer/", organizer_refund_requests),           # ORGANIZER LIST
    path("<int:refund_id>/approve/", approve_refund),        # ORGANIZER
    path("<int:refund_id>/reject/", reject_refund),          # ORGANIZER
]