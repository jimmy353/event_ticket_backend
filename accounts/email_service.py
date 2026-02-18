import os
import requests

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

def send_otp_email(to_email, otp):
    if not SENDGRID_API_KEY:
        raise Exception("SENDGRID_API_KEY missing")

    url = "https://api.sendgrid.com/v3/mail/send"

    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": "Your Sirheart OTP Code",
            }
        ],
        "from": {"email": "noreply@sirheartevents.com", "name": "Sirheart Events"},
        "content": [
            {
                "type": "text/plain",
                "value": f"Your OTP code is: {otp}\n\nThis code will expire in 5 minutes."
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    res = requests.post(url, json=payload, headers=headers, timeout=10)

    if res.status_code not in [200, 202]:
        raise Exception(f"SendGrid error: {res.status_code} {res.text}")
