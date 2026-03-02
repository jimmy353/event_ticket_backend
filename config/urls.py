# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView


def api_home(request):
    return JsonResponse({"message": "Sirheart Events API is running ✅"})


urlpatterns = [
    # API root
    path("", api_home),
    path("api/", api_home),

    # Admin
    path("admin/", admin.site.urls),

    # AUTH ROUTES (accounts handles register + login)
    path("api/auth/", include("accounts.urls")),

    # JWT refresh (keep this)
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # App routes
    path("api/events/", include("events.urls")),
    path("api/tickets/", include("tickets.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/payouts/", include("payouts.urls")),
    path("api/organizer/", include("organizer.urls")),
    path("api/refunds/", include("refunds.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)