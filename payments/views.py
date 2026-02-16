from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Payment
from .serializers import InitiatePaymentSerializer, PaymentSerializer
from .paypack_utils import paypack_service
import uuid
import time
import threading

def simulate_payment_processing(payment_id):
    """
    Simulate backend processing delay and success for CARD payments only
    """
    time.sleep(5) # Simulate 5 seconds delay
    try:
        payment = Payment.objects.get(id=payment_id)
        # Mock logic: if amount is 12345, fail it, otherwise succeed
        if payment.amount == 12345:
             payment.status = 'failed'
        else:
            payment.status = 'successful'
        payment.save()
    except Payment.DoesNotExist:
        pass

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def initiate_payment(request):
    serializer = InitiatePaymentSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        
        # Handle card specifics
        card_number_masked = None
        if data.get('paymentMethod') == 'card':
            card_num = data.get('cardNumber')
            if card_num:
                card_number_masked = f"**** **** **** {card_num[-4:]}"
        
        # Create payment record
        transaction_id = data.get('reference') or str(uuid.uuid4())
        payment = Payment.objects.create(
            transaction_id=transaction_id,
            amount=data['amount'],
            currency=data.get('currency', 'RWF'),
            payment_method=data.get('paymentMethod', 'momo'),
            phone_number=data.get('phoneNumber'),
            card_number_masked=card_number_masked,
            customer_name=data.get('customerName'),
            customer_email=data.get('customerEmail'),
            provider=data.get('provider', 'mtn_rwanda'),
            status='pending'
        )
        
        # Determine payment flow
        if payment.payment_method == 'momo':
            # Use Paypack for Mobile Money
            result = paypack_service.cashin(payment.amount, payment.phone_number)
            if result['ok']:
                payment.provider_reference = result['ref']
                payment.status = result['status'] # usually 'pending'
                payment.save()
            else:
                payment.status = 'failed'
                payment.save()
                return Response({
                    'status': 'failed',
                    'message': result.get('error', 'Payment initiation failed'),
                    'details': result.get('details')
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Keep simulation for Card payments (for now)
            thread = threading.Thread(target=simulate_payment_processing, args=(payment.id,))
            thread.start()
        
        return Response({
            'transactionId': payment.transaction_id,
            'status': payment.status,
            'message': 'Payment initiated successfully'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def check_payment_status(request, transaction_id):
    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
        
        # If pending and has provider ref, check real status on Paypack
        if payment.status == 'pending' and payment.provider_reference and payment.payment_method == 'momo':
             tx_data = paypack_service.check_status(payment.provider_reference)
             if tx_data:
                 new_status = tx_data.get('status')
                 # Map Paypack status if needed, assuming match for now
                 if new_status in ['successful', 'failed', 'completed']:
                     if new_status == 'completed':
                         new_status = 'successful'
                     payment.status = new_status
                     payment.save()

        return Response({
            'transactionId': payment.transaction_id,
            'status': payment.status,
            'message': f'Payment is {payment.status}'
        })
    except Payment.DoesNotExist:
        return Response({
            'message': 'Payment not found'
        }, status=status.HTTP_404_NOT_FOUND)
