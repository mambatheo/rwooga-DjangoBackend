from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class InitiatePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=10, default='RWF')
    paymentMethod = serializers.ChoiceField(choices=['momo', 'card'], default='momo')
    
    # MoMo specific
    phoneNumber = serializers.CharField(max_length=20, required=False)
    
    # Card specific
    cardNumber = serializers.CharField(max_length=20, required=False, write_only=True)
    expiryDate = serializers.CharField(max_length=5, required=False, write_only=True) # MM/YY
    cvv = serializers.CharField(max_length=4, required=False, write_only=True)
    
    customerName = serializers.CharField(max_length=255, required=False)
    customerEmail = serializers.EmailField(required=False)
    reference = serializers.CharField(max_length=100)
    provider = serializers.CharField(max_length=50, default='mtn_rwanda')
    callback_url = serializers.URLField(required=False)
