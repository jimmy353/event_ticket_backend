from django.urls import path
from .views import initiate_payment, organizer_payments

urlpatterns = [
    path("initiate/", initiate_payment, name="initiate-payment"),
    path("organizer/", organizer_payments, name="organizer-payments"),
]