import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_email(to_email, subject, message):
    api_key = os.getenv("SENDGRID_API_KEY")

    if not api_key:
        raise Exception("SENDGRID_API_KEY is missing")

    mail = Mail(
        from_email="Sirheart Events <noreply@sirheartevents.com>",
        to_emails=to_email,
        subject=subject,
        plain_text_content=message,
    )

    sg = SendGridAPIClient(api_key)
    sg.send(mail)
