from django.urls import path
from .views import initiate_payment, organizer_payments
from .views_momo import momo_request_payment, momo_check_status
from .views_momo_order import momo_pay_order, momo_confirm_order
from .views import get_saved_payments, add_saved_payment
from .views import get_default_payment


urlpatterns = [
    path("initiate/", initiate_payment, name="initiate-payment"),
    path("organizer/", organizer_payments, name="organizer-payments"),
    path("momo/request/", momo_request_payment),
    path("momo/status/<str:reference_id>/", momo_check_status),
    path("momo/pay-order/", momo_pay_order),
    path("momo/confirm/<str:reference_id>/", momo_confirm_order),
    path("saved/", get_saved_payments),
    path("saved/add/", add_saved_payment),
    path("saved/default/", get_default_payment),
]