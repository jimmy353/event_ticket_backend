from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

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
    OrganizerSettingsSerializer,
)
from .models import OrganizerRequest, EmailOTP, OrganizerSettings

# ✅ required for UpcomingEventsView (adjust import if your Order model is elsewhere)
from orders.models import Order

User = get_user_model()


# ==========================================
# SEND EMAIL (SENDGRID WEB API)
# ==========================================
def send_email_sendgrid(to_email: str, subject: str, text_content: str) -> tuple[bool, str]:
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
# REGISTER
# ==========================================
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        EmailOTP.objects.filter(
            email=user.email,
            purpose="verify",
            is_used=False
        ).delete()

        otp_obj = EmailOTP.objects.create(
            email=user.email,
            purpose="verify"
        )

        ok, err = send_otp_email(user.email, otp_obj.otp_code)

        return Response(
            {
                "message": "Account created. OTP sent to your email.",
                "email": user.email,
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

        user = User.objects.get(email=email)

        user.is_verified = True
        user.save(update_fields=["is_verified"])

        otp_obj.is_used = True
        otp_obj.save(update_fields=["is_used"])

        return Response(
            {"message": "Email verified successfully. You can now login."},
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
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.is_verified:
            return Response(
                {"message": "Account already verified"},
                status=status.HTTP_200_OK
            )

        EmailOTP.objects.filter(
            email=email,
            purpose="verify",
            is_used=False
        ).delete()

        otp_obj = EmailOTP.objects.create(
            email=email,
            purpose="verify"
        )

        send_otp_email(email, otp_obj.otp_code)

        return Response(
            {"message": "New OTP sent"},
            status=status.HTTP_200_OK
        )


# ==========================================
# LOGIN
# ==========================================
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"detail": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)

        if not user:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_verified:
            return Response(
                {"status": "not_verified"},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


# ==========================================
# PROFILE
# ==========================================
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.user

        email = request.data.get("email")

        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # prevent duplicate emails
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            return Response(
                {"error": "Email already in use"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.email = email
        user.is_verified = False  # force re-verify if email changes
        user.save(update_fields=["email", "is_verified"])

        # delete old verify OTP
        EmailOTP.objects.filter(
            email=email,
            purpose="verify",
            is_used=False
        ).delete()

        EmailOTP.objects.create(
            email=email,
            purpose="verify"
        )

        return Response(
            {"message": "Email updated. Please verify your new email."},
            status=status.HTTP_200_OK
        )


# ==========================================
# CHANGE PASSWORD
# ==========================================
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user

        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not current_password or not new_password or not confirm_password:
            return Response(
                {"error": "All fields are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(current_password):
            return Response(
                {"error": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {"error": "New passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST
            )

        validate_password(new_password, user)

        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password updated successfully"},
            status=status.HTTP_200_OK
        )


# ==========================================
# UPCOMING EVENTS
# ==========================================
class UpcomingEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()

        orders = (
            Order.objects
            .filter(
                user=request.user,
                status="paid",
                event__start_date__gt=now
            )
            .select_related("event")
            .order_by("event__start_date")
        )

        data = []

        for order in orders:
            data.append({
                "id": order.id,
                "event_title": order.event.title,
                "event_start_date": order.event.start_date,
                "location": order.event.location,
                "ticket_type": order.ticket_type.name,
            })

        return Response(data)


# ==========================================
# ORGANIZER REQUEST (WEB DASHBOARD)
# ==========================================
class OrganizerRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        if request.user.is_organizer:
            return Response(
                {"error": "You are already an organizer"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if OrganizerRequest.objects.filter(user=request.user).exists():
            req = OrganizerRequest.objects.get(user=request.user)
            return Response(
                {
                    "error": "Organizer request already submitted",
                    "status": req.status
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
            status=status.HTTP_201_CREATED
        )

    def get(self, request):

        try:
            req = OrganizerRequest.objects.get(user=request.user)
        except OrganizerRequest.DoesNotExist:
            return Response(
                {"status": "not_requested"},
                status=status.HTTP_200_OK
            )

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
# ORGANIZER SETTINGS (WEB DASHBOARD)
# ==========================================
class OrganizerSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        if not request.user.is_organizer:
            return Response(
                {"error": "Only organizers can access settings"},
                status=status.HTTP_403_FORBIDDEN
            )

        settings_obj, created = OrganizerSettings.objects.get_or_create(
            user=request.user
        )

        serializer = OrganizerSettingsSerializer(
            settings_obj,
            context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):

        if not request.user.is_organizer:
            return Response(
                {"error": "Only organizers can update settings"},
                status=status.HTTP_403_FORBIDDEN
            )

        settings_obj, created = OrganizerSettings.objects.get_or_create(
            user=request.user
        )

        serializer = OrganizerSettingsSerializer(
            settings_obj,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(
            {"message": "Settings updated successfully"},
            status=status.HTTP_200_OK
        )


# ==========================================
# FORGOT PASSWORD
# ==========================================
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

        otp = EmailOTP.objects.create(email=email, purpose="reset")

        send_email_sendgrid(
            email,
            "Reset Password",
            f"Your reset OTP is {otp.otp_code}"
        )

        return Response({"message": "Reset OTP sent"})


# ==========================================
# RESET PASSWORD
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

        user = User.objects.get(email=email)

        user.set_password(new_password)
        user.save()

        otp_obj.is_used = True
        otp_obj.save(update_fields=["is_used"])

        return Response({"message": "Password reset successful."})