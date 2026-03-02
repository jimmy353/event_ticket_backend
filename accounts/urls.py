from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    VerifyOTPView,
    ResendOTPView,
    ForgotPasswordView,
    ResetPasswordView,
    ProfileView,
    OrganizerRequestView,
    OrganizerSettingsView,
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),

    path("verify-otp/", VerifyOTPView.as_view()),
    path("resend-otp/", ResendOTPView.as_view()),

    path("forgot-password/", ForgotPasswordView.as_view()),
    path("reset-password/", ResetPasswordView.as_view()),

    path("profile/", ProfileView.as_view()),

    # WEB ONLY
    path("organizer-request/", OrganizerRequestView.as_view()),
    path("organizer/settings/", OrganizerSettingsView.as_view()),
]