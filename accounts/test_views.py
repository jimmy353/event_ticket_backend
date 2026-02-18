from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings


class TestEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        send_mail(
            subject="Sirheart Test Email",
            message="If you received this, SMTP is working!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["yourgmail@gmail.com"],  # change to your email
            fail_silently=False
        )

        return Response({"message": "Test email sent successfully"})
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings


class TestEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        send_mail(
            subject="Sirheart Test Email",
            message="If you received this, SMTP is working!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["jimelias213@gmail.com"],  # change to your email
            fail_silently=False
        )

        return Response({"message": "Test email sent successfully"})
