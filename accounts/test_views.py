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
                message="If you received this email, SMTP is working perfectly ✅",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["jeli05319@gmail.com"],
                fail_silently=False,
            )

            return Response({"message": "Test email sent successfully ✅"})

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=500
            )
