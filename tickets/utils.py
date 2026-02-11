import qrcode
from io import BytesIO
from django.core.files.base import ContentFile


def generate_ticket_qr(data: str):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    return ContentFile(buffer.getvalue())


# IMPORTANT: payments app imports this
def generate_qr_code(data: str):
    return generate_ticket_qr(data)