from django.urls import path
from .views import (
    EventListAPIView,
    OrganizerEventListAPIView,
    OrganizerCreateEventAPIView,
    OrganizerEventDetailAPIView,
)

urlpatterns = [
    path("", EventListAPIView.as_view(), name="events-list"),

    # 🔥 Change this from "organizer/" to "my/"
    path("my/", OrganizerEventListAPIView.as_view(), name="organizer-events"),

    path("create/", OrganizerCreateEventAPIView.as_view(), name="organizer-create-event"),

    path("<int:pk>/", OrganizerEventDetailAPIView.as_view(), name="organizer-event-detail"),
]