from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.conf import settings

from .serializers import (
    RegisterSerializer,
    ProfileSerializer,
    OrganizerRequestSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)

from .models import OrganizerRequest, EmailOTP

User = get_user_model()


# ==========================
# SEND OTP EMAIL FUNCTION
# ==========================
def send_otp_email(email, otp_code, purpose="verify"):
    if purpose == "verify":
        subject = "Verify your Sirheart Events account"
        message = f"""
Hello,

Your verification OTP code is: {otp_code}

This code will expire in 10 minutes.

If you did not create this account, ignore this email.

Sirheart Events Team
"""
    else:
        subject = "Reset your Sirheart Events password"
        message = f"""
Hello,

Your password reset OTP code is: {otp_code}

This code will expire in 10 minutes.

If you did not request a password reset, ignore this email.

Sirheart Events Team
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


# ==========================
# REGISTER (SEND OTP)
# ==========================
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        role = request.data.get("role", "customer")

        # delete old OTPs
        EmailOTP.objects.filter(email=user.email, purpose="verify", is_used=False).delete()

        # create new OTP
        otp_obj = EmailOTP.objects.create(email=user.email, purpose="verify")

        # send OTP
        try:
            send_otp_email(user.email, otp_obj.otp_code, purpose="verify")
        except Exception as e:
            # rollback user creation if email failed
            user.delete()
            return Response(
                {"error": f"Failed to send OTP email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Account created successfully. OTP sent to your email.",
                "email": user.email,
                "role": role,
            },
            status=status.HTTP_201_CREATED,
        )


# ==========================
# VERIFY EMAIL OTP
# ==========================
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        otp_obj = serializer.validated_data["otp_obj"]
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user.is_verified = True
        user.save()

        otp_obj.is_used = True
        otp_obj.save()

        return Response(
            {"message": "Email verified successfully. You can now login."},
            status=status.HTTP_200_OK,
        )


# ==========================
# RESEND OTP
# ==========================
class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({"message": "Account already verified"}, status=status.HTTP_200_OK)

        # delete old OTP
        EmailOTP.objects.filter(email=email, purpose="verify", is_used=False).delete()

        # create new OTP
        otp_obj = EmailOTP.objects.create(email=email, purpose="verify")

        # send OTP
        try:
            send_otp_email(email, otp_obj.otp_code, purpose="verify")
        except Exception as e:
            return Response(
                {"error": f"Failed to resend OTP: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "New OTP sent successfully"},
            status=status.HTTP_200_OK,
        )


# ==========================
# LOGIN WITH ROLE
# ==========================
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

        user = authenticate(username=email, password=password)

        if not user:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # block login if not verified
        if not user.is_verified:
            return Response(
                {
                    "detail": "Email not verified. Please verify your email OTP first.",
                    "status": "not_verified",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ==========================
        # ORGANIZER LOGIN CHECK
        # ==========================
        if role == "organizer":

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

            if user.is_organizer:
                return Response(
                    {
                        "detail": "This account is an organizer. Switch to Organizer tab.",
                        "status": "wrong_role",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

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


# ==========================
# FORGOT PASSWORD (SEND OTP)
# ==========================
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        EmailOTP.objects.filter(email=email, purpose="reset", is_used=False).delete()
        otp_obj = EmailOTP.objects.create(email=email, purpose="reset")

        try:
            send_otp_email(email, otp_obj.otp_code, purpose="reset")
        except Exception as e:
            return Response(
                {"error": f"Failed to send reset OTP: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "Password reset OTP sent successfully"},
            status=status.HTTP_200_OK,
        )


# ==========================
# RESET PASSWORD (VERIFY OTP + SET PASSWORD)
# ==========================
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        new_password = serializer.validated_data["new_password"]
        otp_obj = serializer.validated_data["otp_obj"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()

        otp_obj.is_used = True
        otp_obj.save()

        return Response(
            {"message": "Password reset successful. You can now login."},
            status=status.HTTP_200_OK,
        )


# ==========================
# PROFILE
# ==========================
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)


# ==========================
# ORGANIZER REQUEST
# ==========================
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

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
