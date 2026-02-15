from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

from django.shortcuts import get_object_or_404

from .models import Event
from .serializers import (
    EventListSerializer,
    OrganizerEventSerializer,
    EventCreateSerializer,
)


# ===============================
# PUBLIC EVENTS LIST (GET)
# ===============================
class EventListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        events = Event.objects.all().order_by("-start_date")
        serializer = EventListSerializer(events, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# ===============================
# ORGANIZER EVENTS LIST (GET)
# ===============================
class OrganizerEventListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.filter(organizer=request.user).order_by("-start_date")
        serializer = OrganizerEventSerializer(events, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# ===============================
# CREATE EVENT (POST)
# ===============================
class OrganizerCreateEventAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = EventCreateSerializer(data=request.data)

        if serializer.is_valid():
            event = serializer.save(organizer=request.user)

            return Response(
                OrganizerEventSerializer(event, context={"request": request}).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# SINGLE EVENT (GET, PUT, DELETE)
# ===============================
class OrganizerEventDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, request, pk):
        # Only allow organizer to access their own event
        return get_object_or_404(Event, pk=pk, organizer=request.user)

    def get(self, request, pk):
        event = self.get_object(request, pk)
        serializer = OrganizerEventSerializer(event, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        event = self.get_object(request, pk)

        serializer = EventCreateSerializer(event, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                OrganizerEventSerializer(event, context={"request": request}).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        event = self.get_object(request, pk)
        event.delete()
        return Response({"message": "Event deleted successfully"}, status=status.HTTP_200_OK)