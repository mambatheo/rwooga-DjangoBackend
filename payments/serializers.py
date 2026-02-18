from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
import uuid
from .models import Payment
from orders.models import Order


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payment details"""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    is_successful = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    can_be_retried = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'transaction_id',
            'order',
            'order_number',
            'user',
            'user_name',
            'amount',
            'currency',
            'payment_method',
            'payment_method_display',
            'provider',
            'provider_display',
            'phone_number',
            'card_number_masked',
            'card_type',
            'customer_name',
            'customer_email',
            'status',
            'status_display',
            'is_successful',
            'is_pending',
            'can_be_retried',
            'failure_reason',
            'provider_reference',
            'created_at',
            'updated_at',
            'completed_at',
            'expires_at',
        ]
        read_only_fields = [
            'id',
            'transaction_id',
            'user',
            'status',
            'failure_reason',
            'provider_reference',
            'created_at',
            'updated_at',
            'completed_at',
        ]


class MobileMoneyPaymentSerializer(serializers.Serializer):
    """Serializer for initiating Mobile Money payment"""
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        help_text="Order ID to pay for"
    )
    phone_number = serializers.CharField(
        max_length=20,
        help_text="Phone number in format: 250788123456"
    )
    provider = serializers.ChoiceField(
        choices=[
            ('mtn_rwanda', 'MTN Rwanda'),
            ('airtel_rwanda', 'Airtel Money'),
            ('paypack', 'Paypack'),
        ],
        default='paypack'
    )
    customer_name = serializers.CharField(max_length=255, required=False)
    customer_email = serializers.EmailField(required=False)
    callback_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate_phone_number(self, value):
        """Validate Rwanda phone number format"""
        # Remove spaces and special characters
        phone = value.replace(' ', '').replace('-', '').replace('+', '')
        
        # Check if it's a valid Rwanda number
        if not phone.startswith('250'):
            if phone.startswith('0'):
                # Convert 07XX to 2507XX
                phone = '250' + phone[1:]
            else:
                raise serializers.ValidationError(
                    "Invalid Rwanda phone number. Must start with 250 or 07/08"
                )
        
        if len(phone) != 12:
            raise serializers.ValidationError(
                "Phone number must be 12 digits (including country code 250)"
            )
        
        return phone
    
    def validate_order(self, value):
        """Validate order can be paid"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")
        
        user = request.user
        
        # Check order belongs to user (unless admin)
        if not (user.is_staff or getattr(user, 'is_admin', False)):
            if value.user != user:
                raise serializers.ValidationError("You can only pay for your own orders.")
        
        # Check order status
        if value.status != 'PENDING':
            raise serializers.ValidationError(
                f"Cannot pay for order with status '{value.get_status_display()}'. Only PENDING orders can be paid."
            )
        
        # Check if there's already a successful payment
        if value.payments.filter(status='successful').exists():
            raise serializers.ValidationError("This order has already been paid.")
        
        # Check if there's a recent pending payment (within last 10 minutes)
        recent_pending = value.payments.filter(
            status__in=['pending', 'processing'],
            created_at__gte=timezone.now() - timezone.timedelta(minutes=10)
        )
        if recent_pending.exists():
            raise serializers.ValidationError(
                "There is already a pending payment for this order. Please wait or cancel it first."
            )
        
        return value
    
    def validate(self, attrs):
        """Additional validation"""
        order = attrs.get('order')
        
        # Ensure order amount is positive
        if order and order.final_amount <= 0:
            raise serializers.ValidationError("Order amount must be greater than zero")
        
        return attrs
    
    def create(self, validated_data):
        """Create payment record"""
        order = validated_data['order']
        request = self.context['request']
        user = request.user
        
        # Generate unique transaction ID
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_suffix = uuid.uuid4().hex[:8].upper()
        transaction_id = f"PAY-{timestamp}-{random_suffix}"
        
        # Generate idempotency key
        idempotency_key = f"{order.id}-{timestamp}"
        
        # Create payment
        payment = Payment.objects.create(
            transaction_id=transaction_id,
            order=order,
            user=user,
            amount=order.final_amount,
            currency='RWF',
            payment_method='momo',
            provider=validated_data['provider'],
            phone_number=validated_data['phone_number'],
            customer_name=validated_data.get('customer_name', user.full_name if hasattr(user, 'full_name') else user.username),
            customer_email=validated_data.get('customer_email', user.email),
            callback_url=validated_data.get('callback_url', ''),
            status='pending',
            idempotency_key=idempotency_key,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],  
        )
        
        return payment


class CardPaymentSerializer(serializers.Serializer):
  
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        help_text="Order ID to pay for"
    )
   
    payment_token = serializers.CharField(
        max_length=255,
        help_text="Payment token from gateway (IremoboPay, Paystack, etc.)"
    )
    provider = serializers.ChoiceField(
         choices=[
        ('iremboPay', 'IremoboPay'),
        ('k_pay', 'K-Pay'),
        ('paypack', 'Paypack'),
    ],
    default='iremboPay'
       
    )
    customer_email = serializers.EmailField(required=False)
    callback_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate_order(self, value):
        """Validate order can be paid"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")
        
        user = request.user
        
        # Check order belongs to user (unless admin)
        if not (user.is_staff or getattr(user, 'is_admin', False)):
            if value.user != user:
                raise serializers.ValidationError("You can only pay for your own orders.")
        
        # Check order status
        if value.status != 'PENDING':
            raise serializers.ValidationError(
                f"Cannot pay for order with status '{value.get_status_display()}'. Only PENDING orders can be paid."
            )
        
        # Check if there's already a successful payment
        if value.payments.filter(status='successful').exists():
            raise serializers.ValidationError("This order has already been paid.")
        
        return value
    
    def create(self, validated_data):
        """Create payment record for card payment"""
        order = validated_data['order']
        request = self.context['request']
        user = request.user
        
        # Generate unique transaction ID
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_suffix = uuid.uuid4().hex[:8].upper()
        transaction_id = f"CARD-{timestamp}-{random_suffix}"
        
        # Generate idempotency key
        idempotency_key = f"{order.id}-card-{timestamp}"
        
        # Create payment
        payment = Payment.objects.create(
            transaction_id=transaction_id,
            order=order,
            user=user,
            amount=order.final_amount,
            currency='RWF',
            payment_method='card',
            provider=validated_data['provider'],
            customer_email=validated_data.get('customer_email', user.email),
            callback_url=validated_data.get('callback_url', ''),
            status='processing',  # Card payments start as processing
            idempotency_key=idempotency_key,
            metadata={'payment_token': validated_data['payment_token']},  # Store token in metadata
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
        
        return payment


class PaymentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating payment status (webhooks)"""
    status = serializers.ChoiceField(
        choices=['successful', 'failed', 'processing', 'cancelled']
    )
    provider_reference = serializers.CharField(max_length=100, required=False)
    failure_reason = serializers.CharField(required=False, allow_blank=True)
    provider_response = serializers.JSONField(required=False)
    webhook_data = serializers.JSONField(required=False)