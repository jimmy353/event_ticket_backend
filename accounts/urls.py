# accounts/urls.py
from django.urls import path
from .views import (
    RegisterView,
    LoginWithRoleView,
    VerifyOTPView,
    ResendOTPView,
    ForgotPasswordView,
    ResetPasswordView,
    ProfileView,
    OrganizerRequestView,
    TestEmailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginWithRoleView.as_view()),

    path("verify-otp/", VerifyOTPView.as_view()),
    path("resend-otp/", ResendOTPView.as_view()),

    path("forgot-password/", ForgotPasswordView.as_view()),
    path("reset-password/", ResetPasswordView.as_view()),

    path("profile/", ProfileView.as_view()),
    path("organizer-request/", OrganizerRequestView.as_view()),

    path("test-email/", TestEmailView.as_view()),
]
