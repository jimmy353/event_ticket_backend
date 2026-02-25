from django.urls import path
from .views import (
    request_refund,
    my_refunds,
    admin_refunds,
    approve_refund,
    mark_refund_paid,
)

urlpatterns = [
    path("request/", request_refund),
    path("me/", my_refunds),

    # admin
    path("admin/", admin_refunds),
    path("admin/<str:reference>/approve/", approve_refund),
    path("admin/<str:reference>/paid/", mark_refund_paid),
]