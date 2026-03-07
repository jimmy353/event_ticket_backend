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
    ChangePasswordView,
    save_push_token,
    send_marketing_push,
    push_new_event,
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),

    path("verify-otp/", VerifyOTPView.as_view()),
    path("resend-otp/", ResendOTPView.as_view()),

    path("forgot-password/", ForgotPasswordView.as_view()),
    path("reset-password/", ResetPasswordView.as_view()),

    path("profile/", ProfileView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),

    path("save-push-token/", save_push_token),
    path("marketing-push/", send_marketing_push),
    path("push/event-created/", push_new_event),

    # WEB ONLY
    path("organizer-request/", OrganizerRequestView.as_view()),
    path("organizer/settings/", OrganizerSettingsView.as_view()),
]