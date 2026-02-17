import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from orders.models import Order
from .momo_service import MoMoService


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def momo_pay_order(request):
    """
    Request MoMo payment for an order
    """
    try:
        order_id = request.data.get("order_id")
        phone = request.data.get("phone")

        if not order_id or not phone:
            return Response({"error": "order_id and phone are required"}, status=400)

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.status == "paid":
            return Response({"error": "Order already paid"}, status=400)

        reference_id = str(uuid.uuid4())

        momo_result = MoMoService.request_to_pay(
            amount=order.total_amount,
            currency="EUR",
            phone=phone,
            external_id=order.id,
            payer_message="Ticket Payment",
            payee_note=f"Order #{order.id} Sirheart Events",
            reference_id=reference_id
        )

        order.momo_reference_id = reference_id
        order.payment_status = "PENDING"
        order.payment_method = "MOMO"
        order.save()

        return Response({
            "message": "MoMo payment request sent",
            "order_id": order.id,
            "reference_id": reference_id,
            "status": "PENDING"
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def momo_confirm_order(request, reference_id):
    """
    Confirm MoMo payment and mark order as paid
    """
    try:
        momo_status = MoMoService.get_payment_status(reference_id)

        try:
            order = Order.objects.get(momo_reference_id=reference_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found for this reference"}, status=404)

        order.payment_status = momo_status.get("status", "PENDING")

        if momo_status.get("status") == "SUCCESSFUL":
            order.status = "paid"
            order.financial_transaction_id = momo_status.get("financialTransactionId")

        order.save()

        return Response({
            "order_id": order.id,
            "payment_status": order.payment_status,
            "order_status": order.status,
            "financialTransactionId": order.financial_transaction_id,
            "momo_response": momo_status
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)
