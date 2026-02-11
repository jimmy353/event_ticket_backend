from .base import PaymentProvider


class MockPaymentProvider(PaymentProvider):
    def charge(self, *, amount, reference):
        return {
            "status": "success",
            "reference": reference
        }
