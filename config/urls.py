from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

from accounts.jwt_views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView


def api_home(request):
    return JsonResponse({"message": "Sirheart Events API is running ✅"})


urlpatterns = [
    # API root (returns JSON, not HTML)
    path("", api_home),
    path("api/", api_home),

    path("admin/", admin.site.urls),

    # JWT LOGIN + REFRESH
    path("api/auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # accounts routes
    path("api/auth/", include("accounts.urls")),

    # app routes
    path("api/events/", include("events.urls")),
    path("api/tickets/", include("tickets.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/organizer/", include("organizer.urls")),
    path("api/refunds/", include("refunds.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)