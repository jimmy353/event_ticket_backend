from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from rest_framework import status
from .models import OrganizerRequest
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(["POST"])
def login_role(request):
    email = request.data.get("email")
    password = request.data.get("password")
    role = request.data.get("role")

    user = authenticate(email=email, password=password)

    if not user:
        return Response({"detail": "Invalid credentials"}, status=400)

    # ORGANIZER LOGIN
    if role == "organizer":

        # check if request exists
        try:
            organizer_request = OrganizerRequest.objects.get(user=user)
        except OrganizerRequest.DoesNotExist:
            return Response({"status": "not_requested"}, status=403)

        # check verification
        if not user.is_active:
            return Response({"status": "not_verified"}, status=403)

        # check status
        if organizer_request.status == "pending":
            return Response({"status": "pending"}, status=403)

        if organizer_request.status == "rejected":
            return Response({"status": "rejected"}, status=403)

        if organizer_request.status != "approved":
            return Response({"status": "not_requested"}, status=403)

    # SUCCESS
    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "role": "organizer" if user.is_organizer else "customer"
    })