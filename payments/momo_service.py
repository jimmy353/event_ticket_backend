import base64
import requests
from django.conf import settings


class MoMoService:
    @staticmethod
    def get_access_token():
        """
        Get MoMo sandbox access token (Collections)
        """
        url = f"{settings.MOMO_BASE_URL}/collection/token/"

        credentials = f"{settings.MOMO_API_USER}:{settings.MOMO_API_KEY}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Ocp-Apim-Subscription-Key": settings.MOMO_SUBSCRIPTION_KEY,
        }

        response = requests.post(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"MoMo Token Error: {response.text}")

        return response.json()["access_token"]

    @staticmethod
    def request_to_pay(amount, currency, phone, external_id, payer_message, payee_note, reference_id):
        """
        Request payment from user (Collections)
        """
        token = MoMoService.get_access_token()

        url = f"{settings.MOMO_BASE_URL}/collection/v1_0/requesttopay"

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": reference_id,
            "X-Target-Environment": settings.MOMO_ENVIRONMENT,
            "Ocp-Apim-Subscription-Key": settings.MOMO_SUBSCRIPTION_KEY,
            "Content-Type": "application/json",
        }

        payload = {
            "amount": str(amount),
            "currency": currency,
            "externalId": str(external_id),
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone
            },
            "payerMessage": payer_message,
            "payeeNote": payee_note
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code not in [202, 201]:
            raise Exception(f"MoMo RequestToPay Error: {response.text}")

        return {"reference_id": reference_id, "status": "PENDING"}

    @staticmethod
    def get_payment_status(reference_id):
        """
        Check payment status
        """
        token = MoMoService.get_access_token()

        url = f"{settings.MOMO_BASE_URL}/collection/v1_0/requesttopay/{reference_id}"

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Target-Environment": settings.MOMO_ENVIRONMENT,
            "Ocp-Apim-Subscription-Key": settings.MOMO_SUBSCRIPTION_KEY,
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"MoMo Status Error: {response.text}")

        return response.json()
