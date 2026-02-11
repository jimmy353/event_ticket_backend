import uuid


def request_momo_payment(phone, amount):
    """
    Sandbox / fake MoMo request
    Replace with real API later
    """
    return {
        "success": True,
        "reference": str(uuid.uuid4()),
    }
