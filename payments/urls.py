from django.urls import path
from .views import initiate_payment, organizer_payments
from .views_momo import momo_request_payment, momo_check_status

urlpatterns = [
    path("initiate/", initiate_payment, name="initiate-payment"),
    path("organizer/", organizer_payments, name="organizer-payments"),
    path("momo/request/", momo_request_payment),
    path("momo/status/<str:reference_id>/", momo_check_status),
]