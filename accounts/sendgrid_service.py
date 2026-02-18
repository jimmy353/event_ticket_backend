import os
import requests


SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@sirheartevents.com")


def send_email(to_email, subject, content):
    if not SENDGRID_API_KEY:
        raise Exception("SENDGRID_API_KEY is missing in environment variables")

    url = "https://api.sendgrid.com/v3/mail/send"

    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": subject,
            }
        ],
        "from": {"email": DEFAULT_FROM_EMAIL, "name": "Sirheart Events"},
        "content": [{"type": "text/plain", "value": content}],
    }

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code not in [200, 202]:
        raise Exception(f"SendGrid failed: {response.status_code} {response.text}")

    return True
