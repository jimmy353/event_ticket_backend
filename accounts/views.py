# accounts/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate, get_user_model
from django.conf import settings

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

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


# ==========================================
# SEND EMAIL (SENDGRID WEB API)
# ==========================================
def send_email_sendgrid(to_email: str, subject: str, text_content: str) -> tuple[bool, str]:
    """
    Returns: (success: bool, error_message: str)
    """
    api_key = getattr(settings, "SENDGRID_API_KEY", None)

    if not api_key:
        return False, "SENDGRID_API_KEY is missing in environment variables."

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@sirheartevents.com")

    try:
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=text_content,
        )

        sg = SendGridAPIClient(api_key)
        resp = sg.send(message)

        # SendGrid success: 202 Accepted
        if resp.status_code in (200, 201, 202):
            return True, ""
        return False, f"SendGrid returned status_code={resp.status_code}"

    except Exception as e:
        return False, str(e)


def build_otp_message(otp_code: str, purpose: str) -> tuple[str, str]:
    if purpose == "verify":
        subject = "Verify your Sirheart Events account"
        text = (
            "Hello,\n\n"
            f"Your verification OTP code is: {otp_code}\n\n"
            "This code will expire in 10 minutes.\n\n"
            "If you did not create this account, ignore this email.\n\n"
            "Sirheart Events Team\n"
        )
        return subject, text

    # reset
    subject = "Reset your Sirheart Events password"
    text = (
        "Hello,\n\n"
        f"Your password reset OTP code is: {otp_code}\n\n"
        "This code will expire in 10 minutes.\n\n"
        "If you did not request a password reset, ignore this email.\n\n"
        "Sirheart Events Team\n"
    )
    return subject, text


def send_otp_email(email: str, otp_code: str, purpose: str = "verify") -> tuple[bool, str]:
    subject, text = build_otp_message(otp_code, purpose)
    return send_email_sendgrid(email, subject, text)


# ==========================================
# REGISTER (CREATE USER + SEND OTP)
# ==========================================
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        role = request.data.get("role", "customer")

        # Delete any old unused OTPs
        EmailOTP.objects.filter(email=user.email, purpose="verify", is_used=False).delete()

        # Create new OTP
        otp_obj = EmailOTP.objects.create(email=user.email, purpose="verify")

        # Send OTP
        ok, err = send_otp_email(user.email, otp_obj.otp_code, purpose="verify")

        if not ok:
            # Return message to app, but user still created
            return Response(
                {
                    "message": "Account created but failed to send OTP email.",
                    "email": user.email,
                    "role": role,
                    "email_error": err,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "message": "Account created. OTP sent to your email. Please verify to continue.",
                "email": user.email,
                "role": role,
            },
            status=status.HTTP_201_CREATED,
        )


# ==========================================
# VERIFY EMAIL OTP
# ==========================================
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
        user.save(update_fields=["is_verified"])

        otp_obj.is_used = True
        otp_obj.save(update_fields=["is_used"])

        return Response(
            {"message": "Email verified successfully. You can now login.", "email": user.email},
            status=status.HTTP_200_OK,
        )


# ==========================================
# RESEND OTP
# ==========================================
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

        # Delete old OTPs then create new
        EmailOTP.objects.filter(email=email, purpose="verify", is_used=False).delete()
        otp_obj = EmailOTP.objects.create(email=email, purpose="verify")

        ok, err = send_otp_email(email, otp_obj.otp_code, purpose="verify")

        if not ok:
            return Response(
                {"message": "Failed to resend OTP", "email_error": err},
                status=status.HTTP_200_OK,
            )

        return Response({"message": "New OTP sent to your email"}, status=status.HTTP_200_OK)


# ==========================================
# LOGIN WITH ROLE (BLOCK IF NOT VERIFIED)
# ==========================================
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
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not getattr(user, "is_verified", False):
            return Response(
                {
                    "detail": "Email not verified. Please verify your email OTP first.",
                    "status": "not_verified",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Organizer
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

        # Customer
        if role == "customer":
            if user.is_organizer:
                return Response(
                    {
                        "detail": "This account is an organizer. Switch to Organizer tab.",
                        "status": "wrong_role",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # If they have organizer request, force them to use organizer tab
            if OrganizerRequest.objects.filter(user=user).exists():
                req = OrganizerRequest.objects.get(user=user)
                if req.status in ["pending", "rejected"]:
                    return Response(
                        {
                            "detail": "You have an organizer request. Please login using Organizer tab.",
                            "status": req.status,
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


# ==========================================
# FORGOT PASSWORD (SEND RESET OTP)
# ==========================================
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        # Delete old reset OTPs
        EmailOTP.objects.filter(email=email, purpose="reset", is_used=False).delete()
        otp_obj = EmailOTP.objects.create(email=email, purpose="reset")

        ok, err = send_otp_email(email, otp_obj.otp_code, purpose="reset")

        if not ok:
            return Response(
                {"message": "Failed to send reset OTP", "email_error": err},
                status=status.HTTP_200_OK,
            )

        return Response({"message": "Password reset OTP sent to your email"}, status=status.HTTP_200_OK)


# ==========================================
# RESET PASSWORD (VERIFY OTP + SET NEW PASSWORD)
# ==========================================
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
        otp_obj.save(update_fields=["is_used"])

        return Response({"message": "Password reset successful. You can now login."}, status=status.HTTP_200_OK)


# ==========================================
# PROFILE
# ==========================================
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ==========================================
# ORGANIZER REQUEST
# ==========================================
class OrganizerRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_organizer:
            return Response({"error": "You are already an organizer"}, status=status.HTTP_400_BAD_REQUEST)

        if OrganizerRequest.objects.filter(user=request.user).exists():
            req = OrganizerRequest.objects.get(user=request.user)
            return Response(
                {"error": "Organizer request already submitted", "status": req.status},
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

        return Response({"message": "Organizer request submitted successfully"}, status=status.HTTP_201_CREATED)

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


# ==========================================
# OPTIONAL: TEST EMAIL ENDPOINT
# ==========================================
class TestEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        to = request.GET.get("to") or "noreply@sirheartevents.com"
        ok, err = send_email_sendgrid(
            to_email=to,
            subject="Sirheart Test Email",
            text_content="This is a test email from Sirheart Events backend.",
        )

        if not ok:
            return Response({"ok": False, "error": err}, status=status.HTTP_200_OK)

        return Response({"ok": True, "message": "Test email sent ✅"}, status=status.HTTP_200_OK)
