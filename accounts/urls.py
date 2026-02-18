from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .test_views import TestEmailView


from .views import (
    RegisterView,
    ProfileView,
    OrganizerRequestView,
    LoginWithRoleView,
    VerifyOTPView,
    ResendOTPView,
    ForgotPasswordView,
    ResetPasswordView,
)

urlpatterns = [
    # register
    path("register/", RegisterView.as_view(), name="register"),

    # verify email OTP
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),

    # resend OTP
    path("resend-otp/", ResendOTPView.as_view(), name="resend_otp"),

    # login with role
    path("login-role/", LoginWithRoleView.as_view(), name="login_role"),

    # JWT refresh
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # profile
    path("profile/", ProfileView.as_view(), name="profile"),

    # organizer request
    path("organizer/request/", OrganizerRequestView.as_view(), name="organizer_request"),

    # forgot password OTP
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),

    # reset password using OTP
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),

    path("test-email/", TestEmailView.as_view(), name="test_email"),

]
