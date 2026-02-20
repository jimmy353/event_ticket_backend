from django.urls import path
from .views import (
    create_order,
    my_orders,
    request_refund,
    organizer_orders,
    organizer_refund_requests,
    organizer_approve_refund,
    organizer_dashboard_stats,
    organizer_advanced_analytics,
)

urlpatterns = [
    path("create/", create_order),

    # USER
    path("my/", my_orders),
    path("<int:order_id>/refund/", request_refund),

    # ORGANIZER
    path("organizer/", organizer_orders),
    path("organizer/refunds/", organizer_refund_requests),
    path("organizer/refunds/<int:order_id>/approve/", organizer_approve_refund),
    path("organizer/orders/", organizer_orders),
    path("organizer/dashboard/", organizer_dashboard_stats),
    path("organizer/advanced-analytics/", organizer_advanced_analytics),
]