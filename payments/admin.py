from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Minimal admin interface for Payment model"""
    
    list_display = ['transaction_id', 'order', 'amount', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['transaction_id', 'phone_number', 'order__order_number']
    readonly_fields = ['transaction_id', 'order', 'user', 'amount']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False