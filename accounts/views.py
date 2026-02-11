from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .serializers import (
    RegisterSerializer,
    ProfileSerializer,
    OrganizerRequestSerializer,
)

from .models import OrganizerRequest


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            role = request.data.get("role")

            # ORGANIZER: no tokens, show message only
            if role == "organizer":
                return Response(
                    {
                        "message": "Thank you! We are reviewing your organizer request. Please login after approval in 1 to 3 days."
                    },
                    status=status.HTTP_201_CREATED,
                )

            # CUSTOMER: return tokens immediately
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "Customer registered successfully",
                    "user": ProfileSerializer(user).data,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginWithRoleView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        role = request.data.get("role")

        if not email or not password:
            return Response(
                {"detail": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role not in ["customer", "organizer"]:
            return Response(
                {"detail": "Role must be customer or organizer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # IMPORTANT: authenticate uses USERNAME_FIELD (email in your custom user)
        user = authenticate(username=email, password=password)

        if not user:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ==========================
        # ORGANIZER LOGIN CHECK
        # ==========================
        if role == "organizer":

            # approved organizer
            if user.is_organizer:
                refresh = RefreshToken.for_user(user)
                return Response(
                    {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                        "role": role,
                        "status": "approved",
                    },
                    status=status.HTTP_200_OK,
                )

            # check organizer request status
            if OrganizerRequest.objects.filter(user=user).exists():
                req = OrganizerRequest.objects.get(user=user)

                if req.status == "pending":
                    return Response(
                        {
                            "detail": "Your organizer request is pending. Please wait 1 to 3 days.",
                            "status": "pending",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                if req.status == "rejected":
                    return Response(
                        {
                            "detail": "Your organizer request was rejected. Contact support.",
                            "status": "rejected",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            return Response(
                {
                    "detail": "You have not submitted an organizer request yet.",
                    "status": "not_requested",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ==========================
        # CUSTOMER LOGIN CHECK
        # ==========================
        if role == "customer":

            # approved organizer cannot login as customer
            if user.is_organizer:
                return Response(
                    {
                        "detail": "This account is an organizer. Switch to Organizer tab.",
                        "status": "wrong_role",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # if organizer request exists (pending/rejected) block customer login
            if OrganizerRequest.objects.filter(user=user).exists():
                req = OrganizerRequest.objects.get(user=user)

                if req.status == "pending":
                    return Response(
                        {
                            "detail": "Your organizer request is pending. Please login using Organizer tab.",
                            "status": "pending",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                if req.status == "rejected":
                    return Response(
                        {
                            "detail": "Your organizer request was rejected. Please login using Organizer tab.",
                            "status": "rejected",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

        # login success for customer
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "role": role,
                "status": "approved",
            },
            status=status.HTTP_200_OK,
        )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)


class OrganizerRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_organizer:
            return Response(
                {"error": "You are already an organizer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if OrganizerRequest.objects.filter(user=request.user).exists():
            req = OrganizerRequest.objects.get(user=request.user)
            return Response(
                {
                    "error": "Organizer request already submitted",
                    "status": req.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrganizerRequestSerializer(data=request.data)

        if serializer.is_valid():
            OrganizerRequest.objects.create(
                user=request.user,
                company_name=serializer.validated_data["company_name"],
                momo_number=serializer.validated_data["momo_number"],
                id_document=serializer.validated_data["id_document"],
                status="pending",
            )

            return Response(
                {"message": "Organizer request submitted successfully"},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        try:
            req = OrganizerRequest.objects.get(user=request.user)
        except OrganizerRequest.DoesNotExist:
            return Response({"status": "not_requested"}, status=status.HTTP_200_OK)

        return Response(
            {
                "status": req.status,
                "company_name": req.company_name,
                "momo_number": req.momo_number,
                "id_document": req.id_document.url if req.id_document else None,
            },
            status=status.HTTP_200_OK,
        )