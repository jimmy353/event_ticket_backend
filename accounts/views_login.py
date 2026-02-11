from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class LoginWithRoleView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        role = request.data.get("role")  # customer | organizer

        if not email or not password:
            return Response(
                {"detail": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if role not in ["customer", "organizer"]:
            return Response(
                {"detail": "Invalid role. Must be customer or organizer"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=email, password=password)

        if not user:
            return Response(
                {"detail": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ✅ Role validation
        if role == "organizer" and not user.is_organizer:
            return Response(
                {"detail": "This account is not an organizer"},
                status=status.HTTP_403_FORBIDDEN
            )

        if role == "customer" and user.is_organizer:
            return Response(
                {"detail": "This account is an organizer. Select Organizer."},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "role": role,
                "is_organizer": user.is_organizer
            },
            status=status.HTTP_200_OK
        )