from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model

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
from .sendgrid_email import send_email

User = get_user_model()


# ==========================
# SEND OTP EMAIL (SENDGRID)
# ==========================
def send_otp_email(email, otp_code, purpose="verify"):
    if purpose == "verify":
        subject = "Verify your Sirheart Events account"
        message = f"""
Hello,

Your verification OTP code is:

{otp_code}

This code will expire in 10 minutes.

Sirheart Events Team
"""
    else:
        subject = "Reset your Sirheart Events password"
        message = f"""
Hello,

Your password reset OTP code is:

{otp_code}

This code will expire in 10 minutes.

Sirheart Events Team
"""

    try:
        send_email(email, subject, message)
        print("✅ OTP email sent to:", email)
    except Exception as e:
        print("❌ OTP email failed:", str(e))


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

        # remove old OTPs
        EmailOTP.objects.filter(
            email=user.email,
            purpose="verify",
            is_used=False
        ).delete()

        otp_obj = EmailOTP.objects.create(
            email=user.email,
            purpose="verify"
        )

        send_otp_email(user.email, otp_obj.otp_code, purpose="verify")

        return Response(
            {
                "message": "Account created. OTP sent to your email.",
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

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found"}, status=404)

        user.is_verified = True
        user.save()

        otp_obj.is_used = True
        otp_obj.save()

        return Response(
            {"message": "Email verified successfully"},
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
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found"}, status=404)

        if user.is_verified:
            return Response({"message": "Account already verified"}, status=200)

        EmailOTP.objects.filter(
            email=email,
            purpose="verify",
            is_used=False
        ).delete()

        otp_obj = EmailOTP.objects.create(
            email=email,
            purpose="verify"
        )

        send_otp_email(email, otp_obj.otp_code, purpose="verify")

        return Response({"message": "OTP resent"}, status=200)


# ==========================
# LOGIN WITH ROLE
# ==========================
class LoginWithRoleView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        role = request.data.get("role")

        user = authenticate(username=email, password=password)

        if not user:
            return Response({"detail": "Invalid credentials"}, status=401)

        if not user.is_verified:
            return Response(
                {
                    "detail": "Email not verified",
                    "status": "not_verified",
                },
                status=403,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "role": role,
                "status": "approved",
            },
            status=200,
        )


# ==========================
# FORGOT PASSWORD
# ==========================
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]

        EmailOTP.objects.filter(
            email=email,
            purpose="reset",
            is_used=False
        ).delete()

        otp_obj = EmailOTP.objects.create(
            email=email,
            purpose="reset"
        )

        send_otp_email(email, otp_obj.otp_code, purpose="reset")

        return Response({"message": "Password reset OTP sent"}, status=200)


# ==========================
# RESET PASSWORD
# ==========================
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]
        new_password = serializer.validated_data["new_password"]
        otp_obj = serializer.validated_data["otp_obj"]

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found"}, status=404)

        user.set_password(new_password)
        user.save()

        otp_obj.is_used = True
        otp_obj.save()

        return Response({"message": "Password reset successful"}, status=200)


# ==========================
# PROFILE
# ==========================
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
