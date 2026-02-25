from django.urls import path
from .views import request_refund, approve_refund

urlpatterns = [
    path("request/", request_refund),
    path("approve/<int:order_id>/", approve_refund),
]