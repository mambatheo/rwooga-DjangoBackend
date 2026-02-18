from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Payment
from drf_spectacular.utils import extend_schema
from .serializers import (
    PaymentSerializer,
    MobileMoneyPaymentSerializer,
    CardPaymentSerializer,
    PaymentStatusUpdateSerializer,
)
from .paypack_utils import paypack_service  


class IsAdminOrStaff(permissions.BasePermission):
    """Allow access only to admin or staff users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or getattr(request.user, 'is_admin', False)
        )

@extend_schema(tags=["Payments"])
class PaymentViewSet(viewsets.ModelViewSet):
  
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'provider']
    search_fields = ['transaction_id', 'phone_number', 'customer_name', 'customer_email']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Payment.objects.none()
        if not self.request.user.is_authenticated:
            return Payment.objects.none()
        
        user = self.request.user
        
        # Admin/staff see all payments
        if user.is_staff or getattr(user, 'is_admin', False):
            return Payment.objects.all().select_related('order', 'user')
        
        # Regular users see only their own payments
        return Payment.objects.filter(user=user).select_related('order')
    
    def get_permissions(self):
        """Different permissions for different actions"""
        if self.action in ('update', 'partial_update', 'destroy'):
            # Only admins can update/delete payments
            return [IsAdminOrStaff()]
        return [permissions.IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """Disable direct create - use initiate_momo or initiate_card instead"""
        return Response(
            {
                'error': 'Use /payments/initiate_momo/ or /payments/initiate_card/ to create payments'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'], url_path='initiate-momo')
    def initiate_momo(self, request):
    
        serializer = MobileMoneyPaymentSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Create payment record
        payment = serializer.save()
        
        # Initiate payment with Paypack
        try:
            result = paypack_service.cashin(
                amount=float(payment.amount),
                phone_number=payment.phone_number
            )
            
            if result.get('ok'):
                # Payment initiated successfully
                payment.provider_reference = result.get('ref')
                payment.status = result.get('status', 'pending')
                payment.provider_response = result
                payment.save()
                
                return Response({
                    'transaction_id': payment.transaction_id,
                    'status': payment.status,
                    'message': 'Payment initiated successfully. Please check your phone to complete the payment.',
                    'provider_reference': payment.provider_reference,
                    'expires_at': payment.expires_at,
                }, status=status.HTTP_201_CREATED)
            else:
                # Payment initiation failed
                error_message = result.get('error', 'Payment initiation failed')
                payment.mark_failed(
                    reason=error_message,
                    provider_response=result
                )
                
                return Response({
                    'error': error_message,
                    'details': result.get('details'),
                    'transaction_id': payment.transaction_id,
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # Handle unexpected errors
            payment.mark_failed(reason=f"System error: {str(e)}")
            
            return Response({
                'error': 'An error occurred while initiating payment',
                'details': str(e),
                'transaction_id': payment.transaction_id,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='initiate-card')
    def initiate_card(self, request):
       
        serializer = CardPaymentSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Create payment record
        payment = serializer.save()
        
       
        
        return Response({
            'transaction_id': payment.transaction_id,
            'status': payment.status,
            'message': 'Card payment is being processed',
            'payment_id': str(payment.id),
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'], url_path='status')
    def check_status(self, request, pk=None):
       
        payment = self.get_object()
        
        # If payment is pending and has provider reference, check with Paypack
        if (payment.status in ['pending', 'processing'] and 
            payment.provider_reference and 
            payment.payment_method == 'momo'):
            
            try:
                tx_data = paypack_service.check_status(payment.provider_reference)
                
                if tx_data:
                    new_status = tx_data.get('status')
                    
                    # Map Paypack status to our status
                    if new_status == 'completed':
                        payment.mark_successful(
                            provider_reference=payment.provider_reference,
                            provider_response=tx_data
                        )
                    elif new_status == 'failed':
                        payment.mark_failed(
                            reason=tx_data.get('message', 'Payment failed'),
                            provider_response=tx_data
                        )
                    elif new_status in ['pending', 'processing']:
                        payment.status = new_status
                        payment.provider_response = tx_data
                        payment.save()
            
            except Exception as e:
                # Log error but don't fail the request
                pass
        
        # Check if payment has expired
        if payment.expires_at and timezone.now() > payment.expires_at and payment.is_pending:
            payment.status = 'expired'
            payment.save()
        
        return Response({
            'transaction_id': payment.transaction_id,
            'status': payment.status,
            'status_display': payment.get_status_display(),
            'is_successful': payment.is_successful,
            'is_pending': payment.is_pending,
            'can_be_retried': payment.can_be_retried,
            'amount': payment.amount,
            'created_at': payment.created_at,
            'completed_at': payment.completed_at,
            'failure_reason': payment.failure_reason,
        })
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_payment(self, request, pk=None):
      
        payment = self.get_object()
        
        # Check user owns the payment
        if payment.user != request.user and not (
            request.user.is_staff or getattr(request.user, 'is_admin', False)
        ):
            return Response(
                {'error': 'You do not have permission to cancel this payment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if payment.cancel():
            return Response({
                'message': 'Payment cancelled successfully',
                'transaction_id': payment.transaction_id,
                'status': payment.status,
            })
        else:
            return Response(
                {
                    'error': f'Cannot cancel payment with status "{payment.get_status_display()}"',
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(
        detail=False,
        methods=['post'],
        url_path='webhook',
        permission_classes=[permissions.AllowAny],  # Webhooks come from payment provider
    )
    def webhook(self, request):
    
        data = request.data
        
        # Get transaction reference from webhook data
        # This depends on  payment provider's webhook format
        provider_reference = data.get('ref') or data.get('reference')
        
        if not provider_reference:
            return Response(
                {'error': 'No reference provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payment = Payment.objects.get(provider_reference=provider_reference)
            
            # Update payment based on webhook data
            webhook_status = data.get('status')
            
            if webhook_status == 'successful' or webhook_status == 'completed':
                payment.mark_successful(
                    provider_reference=provider_reference,
                    provider_response=data
                )
            elif webhook_status == 'failed':
                payment.mark_failed(
                    reason=data.get('message', 'Payment failed'),
                    provider_response=data
                )
            
            payment.webhook_data = data
            payment.save()
            
            return Response({'status': 'webhook received'}, status=status.HTTP_200_OK)
        
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )