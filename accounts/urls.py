from django.urls import path

from .views import (
    RegisterView,
    VerifyOTPView,
    ResendOTPView,
    LoginWithRoleView,
    ForgotPasswordView,
    ResetPasswordView,
    ProfileView,
    OrganizerRequestView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("login/", LoginWithRoleView.as_view(), name="login"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("organizer-request/", OrganizerRequestView.as_view(), name="organizer-request"),
]
