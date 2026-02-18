from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings

def send_email(to_email, subject, content):
    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content,
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(message)
