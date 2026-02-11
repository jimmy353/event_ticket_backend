from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Event
from .serializers import (
    EventListSerializer,
    OrganizerEventSerializer,
    EventCreateSerializer,
)


class EventListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        events = Event.objects.all().order_by("-start_date")
        serializer = EventListSerializer(
            events,
            many=True,
            context={"request": request}
        )
        return Response(serializer.data)


class OrganizerEventListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.filter(
            organizer=request.user
        ).order_by("-start_date")

        serializer = OrganizerEventSerializer(
            events,
            many=True,
            context={"request": request}
        )
        return Response(serializer.data)


class OrganizerCreateEventAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = EventCreateSerializer(data=request.data)

        if serializer.is_valid():
            event = serializer.save(organizer=request.user)
            return Response(
                OrganizerEventSerializer(
                    event,
                    context={"request": request}
                ).data,
                status=201
            )

        return Response(serializer.errors, status=400)