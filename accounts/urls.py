from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    ProfileView,
    OrganizerRequestView,
    LoginWithRoleView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),

    # JWT refresh
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # profile
    path("profile/", ProfileView.as_view(), name="profile"),

    # organizer request
    path("organizer/request/", OrganizerRequestView.as_view(), name="organizer_request"),

    # role login
    path("login-role/", LoginWithRoleView.as_view(), name="login_role"),
]