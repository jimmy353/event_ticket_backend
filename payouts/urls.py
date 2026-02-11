from django.urls import path
from .views import MyPayoutsAPIView

urlpatterns = [
    path("my/", MyPayoutsAPIView.as_view(), name="my-payouts"),
]
