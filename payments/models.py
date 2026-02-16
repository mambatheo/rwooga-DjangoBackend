from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Payment(models.Model):
    """Payment model supporting Mobile Money and Card payments"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('momo', 'Mobile Money'),
        ('card', 'Credit/Debit Card'),
    )
    
    PROVIDER_CHOICES = (
        ('mtn_rwanda', 'MTN Rwanda Mobile Money'),
        ('airtel_rwanda', 'Airtel Money Rwanda'),
        ('paypack', 'Paypack'),
        ('flutterwave', 'Flutterwave'),
        ('irembpPay', 'Irembo Pay'),
        ('other', 'Other'),
    )

    # Primary identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    
    # CRITICAL: Link to Order and User
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Order this payment is for"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='RWF')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='momo')
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, default='mtn_rwanda')
    
    # Mobile Money specific
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    
    # Card specific (NEVER store full card numbers - use payment gateway tokens)
    card_number_masked = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Last 4 digits only: **** **** **** 1234"
    )
    card_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Visa, Mastercard, etc."
    )
    
    # Customer info
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    customer_email = models.EmailField(null=True, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    failure_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for payment failure"
    )
    
    # Provider tracking
    provider_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference from payment provider (e.g., Paypack ref)"
    )
    provider_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw response from payment provider"
    )
    
    # Callback/Webhook
    callback_url = models.URLField(null=True, blank=True)
    webhook_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw webhook data from provider"
    )
    
    # Idempotency and security
    idempotency_key = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Prevent duplicate payments"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional payment metadata"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payment was successfully completed"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When pending payment expires"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['order', 'status']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['provider_reference']),
        ]

    def __str__(self):
        return f"{self.transaction_id} - {self.get_payment_method_display()} - {self.status}"
    
    def mark_successful(self, provider_reference=None, provider_response=None):
        """Mark payment as successful and update order"""
        self.status = 'successful'
        self.completed_at = timezone.now()
        
        if provider_reference:
            self.provider_reference = provider_reference
        if provider_response:
            self.provider_response = provider_response
        
        self.save()
        
        # Update order status to PAID
        if self.order:
            self.order.status = 'PAID'
            self.order.paid_at = timezone.now()
            self.order.save()
    
    def mark_failed(self, reason=None, provider_response=None):
        """Mark payment as failed"""
        self.status = 'failed'
        self.failure_reason = reason
        
        if provider_response:
            self.provider_response = provider_response
        
        self.save()
    
    def cancel(self):
        """Cancel pending payment"""
        if self.status in ['pending', 'processing']:
            self.status = 'cancelled'
            self.save()
            return True
        return False
    
    @property
    def is_successful(self):
        """Check if payment is successful"""
        return self.status == 'successful'
    
    @property
    def is_pending(self):
        """Check if payment is pending"""
        return self.status in ['pending', 'processing']
    
    @property
    def can_be_retried(self):
        """Check if payment can be retried"""
        return self.status in ['failed', 'expired', 'cancelled']