from django.urls import path
from .views import OrganizerWalletAPIView

urlpatterns = [
    path("me/", OrganizerWalletAPIView.as_view(), name="organizer-wallet"),
]
