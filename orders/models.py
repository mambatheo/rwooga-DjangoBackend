import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class Shipping(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_phone = models.CharField(max_length=20)
    district = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sector}, {self.district}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=50, unique=True, editable=False, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    shipping_address = models.ForeignKey(Shipping, on_delete=models.SET_NULL, related_name="orders", null=True)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    customer_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            timestamp = timezone.now().strftime('%Y%m%d')
            self.order_number = f"ORD-{timestamp}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def final_amount(self):
        return self.total_amount - self.refunded_amount

    @property
    def can_be_returned(self):
        if self.status != 'DELIVERED' or not self.delivered_at:
            return False
        return (timezone.now() - self.delivered_at).days <= 30

    def __str__(self):
        return f"{self.order_number} - {self.user}"


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='order_items')
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_returned = models.PositiveIntegerField(default=0)
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    @property
    def subtotal(self):
        return self.price_at_purchase * self.quantity

    @property
    def quantity_available_for_return(self):
        return self.quantity - self.quantity_returned

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"


class OrderDiscount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_discounts')
    discount = models.ForeignKey(
        'products.Discount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_discounts'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Discount for {self.order.order_number}"


class Return(models.Model):
    STATUS_CHOICES = [
        ('REQUESTED', 'Return Requested'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    return_number = models.CharField(max_length=50, unique=True, editable=False, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='returns')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='returns')
    reason = models.CharField(max_length=50)
    detailed_reason = models.TextField()
    rejection_reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    requested_refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approved_refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.return_number:
            timestamp = timezone.now().strftime('%Y%m%d')
            self.return_number = f"RTN-{timestamp}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status not in ['COMPLETED', 'CANCELLED', 'REJECTED']

    def approve(self, amount=None):
        self.status = 'APPROVED'
        self.approved_at = timezone.now()
        self.approved_refund_amount = amount or self.requested_refund_amount
        self.save()

    def reject(self, reason):
        self.status = 'REJECTED'
        self.rejection_reason = reason
        self.save()

    def __str__(self):
        return f"{self.return_number} - {self.order.order_number}"


class Refund(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    refund_number = models.CharField(max_length=50, unique=True, editable=False, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.refund_number:
            timestamp = timezone.now().strftime('%Y%m%d')
            self.refund_number = f"REF-{timestamp}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def mark_completed(self, transaction_id=None):
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()
        
        self.order.refunded_amount += self.amount
        self.order.status = 'REFUNDED' if self.order.refunded_amount >= self.order.total_amount else self.order.status
        self.order.save()

    def __str__(self):
        return f"{self.refund_number} - {self.amount}"