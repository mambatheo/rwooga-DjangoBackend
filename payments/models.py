from django.db import models
import uuid

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    )

    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='RWF')
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    payment_method = models.CharField(max_length=20, default='momo', choices=(('momo', 'Mobile Money'), ('card', 'Credit/Debit Card')))
    card_number_masked = models.CharField(max_length=20, null=True, blank=True)
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    customer_email = models.EmailField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    provider = models.CharField(max_length=50, default='mtn_rwanda')
    provider_reference = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.phone_number} - {self.status}"
