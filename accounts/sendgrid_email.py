from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings


class TestEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            send_mail(
                subject="Sirheart Test Email",
                message="Hello Sirheart, this is a test email from your backend.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )

            return Response({"message": "✅ Test email sent successfully!"})

        except Exception as e:
            return Response({"error": str(e)}, status=500)
