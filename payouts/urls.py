from django.urls import path
from .views import (
    MyPayoutsAPIView,
    request_payout,
    approve_payout
)

urlpatterns = [
    path("my/", MyPayoutsAPIView.as_view(), name="my-payouts"),
    path("request/", request_payout, name="request-payout"),
    path("approve/<str:reference>/", approve_payout, name="approve-payout"),
]