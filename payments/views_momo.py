import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .momo_service import MoMoService

# 🔔 PUSH IMPORTS
from accounts.models import PushToken
from utils.push import send_expo_push


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def momo_request_payment(request):
    """
    Request payment from MoMo user
    """
    try:
        amount = request.data.get("amount")
        phone = request.data.get("phone")

        if not amount or not phone:
            return Response(
                {"error": "amount and phone are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        reference_id = str(uuid.uuid4())

        result = MoMoService.request_to_pay(
            amount=amount,
            currency="EUR",  # sandbox uses EUR mostly
            phone=phone,
            external_id=request.user.id,
            payer_message="Event Ticket Payment",
            payee_note="Sirheart Events Ticket",
            reference_id=reference_id
        )

        return Response(result)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def momo_check_status(request, reference_id):
    """
    Check MoMo payment status
    """
    try:

        result = MoMoService.get_payment_status(reference_id)

        # 🔔 SEND PUSH NOTIFICATION IF PAYMENT SUCCESSFUL
        if result.get("status") == "SUCCESSFUL":

            tokens = list(
                PushToken.objects
                .filter(user=request.user)
                .values_list("token", flat=True)
            )

            if tokens:
                send_expo_push(
                    tokens,
                    "Payment Confirmed 💳",
                    "Your ticket payment was successful. Your ticket is ready!"
                )

        return Response(result)

    except Exception as e:
        return Response({"error": str(e)}, status=500)