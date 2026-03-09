import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .momo_service import MoMoService
from payments.models import SavedPaymentMethod

# 🔔 PUSH IMPORTS
from accounts.models import PushToken
from utils.push import send_expo_push


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def momo_request_payment(request):

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
            currency="EUR",
            phone=phone,
            external_id=request.user.id,
            payer_message="Event Ticket Payment",
            payee_note="Sirheart Events Ticket",
            reference_id=reference_id
        )

        # 🔥 AUTO SAVE MOMO NUMBER
        SavedPaymentMethod.objects.get_or_create(
            user=request.user,
            phone_number=phone,
            defaults={
                "provider": "MOMO",
                "is_default": True
            }
        )

        return Response(result)

    except Exception as e:

        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def momo_check_status(request, reference_id):
    """
    Check MoMo payment status
    """

    try:

        result = MoMoService.get_payment_status(reference_id)

        # Payment success
        if result.get("status") == "SUCCESSFUL":

            try:

                # Find order using momo reference
                order = Order.objects.get(momo_reference_id=reference_id)

                # Only update if not already paid
                if order.status != "paid":

                    order.status = "paid"
                    order.payment_status = "SUCCESSFUL"
                    order.financial_transaction_id = result.get("financialTransactionId")

                    order.save()

                # 🔔 Send notification only once
                if not order.notification_sent:

                    tokens = list(
                        PushToken.objects
                        .filter(user=order.user)
                        .values_list("token", flat=True)
                    )

                    if tokens:

                        send_expo_push(
                            tokens,
                            "Payment Confirmed 💳",
                            "Your ticket payment was successful. Your ticket is ready!",
                            {
                                "screen": "MyTickets",
                                "order_id": order.id
                            }
                        )

                        order.notification_sent = True
                        order.save()

            except Order.DoesNotExist:
                pass

        return Response(result)

    except Exception as e:
        return Response({"error": str(e)}, status=500)