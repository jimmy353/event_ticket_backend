from django.urls import path
from .views import (
    EventListAPIView,
    OrganizerEventListAPIView,
    OrganizerCreateEventAPIView,
    OrganizerEventDetailAPIView,
)

urlpatterns = [
    path("", EventListAPIView.as_view(), name="events-list"),
    path("organizer/", OrganizerEventListAPIView.as_view(), name="organizer-events"),
    path("create/", OrganizerCreateEventAPIView.as_view(), name="organizer-create-event"),

    # update/delete/view single event
    path("<int:pk>/", OrganizerEventDetailAPIView.as_view(), name="organizer-event-detail"),
]