from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import requests


class TestEmailView(APIView):
    def get(self, request):
        api_key = os.getenv("SENDGRID_API_KEY")

        if not api_key:
            return Response({"error": "SENDGRID_API_KEY not found in environment"}, status=500)

        url = "https://api.sendgrid.com/v3/mail/send"

        payload = {
            "personalizations": [{"to": [{"email": "sirheartjimmy@gmail.com"}]}],
            "from": {"email": "noreply@sirheartevents.com", "name": "Sirheart Events"},
            "subject": "Sirheart Test Email ✅",
            "content": [{"type": "text/plain", "value": "SendGrid API is working!"}]
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)

            return Response({
                "status_code": r.status_code,
                "response": r.text
            }, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
