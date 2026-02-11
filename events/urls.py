from django.urls import path
from .views import (
    EventListAPIView,
    OrganizerEventListAPIView,
    OrganizerCreateEventAPIView,
)

urlpatterns = [
    path("", EventListAPIView.as_view(), name="events-list"),
    path("organizer/", OrganizerEventListAPIView.as_view(), name="organizer-events"),
    path("create/", OrganizerCreateEventAPIView.as_view(), name="organizer-create-event"),
]