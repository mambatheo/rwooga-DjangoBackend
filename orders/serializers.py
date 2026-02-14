from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_id', 'quantity', 'price_at_purchase']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_amount', 'shipping_fee', 'discount_amount', 'status', 'items', 'created_at']
        read_only_fields = ['user', 'total_amount', 'status']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        # Logic: Calculate total based on items, shipping and discounts
        # In a real scenario, you would fetch prices from Dev 2's Product model
        total = sum(item['price_at_purchase'] * item['quantity'] for item in items_data)
        total = total + validated_data.get('shipping_fee', 0) - validated_data.get('discount_amount', 0)
        
        order = Order.objects.create(total_amount=total, **validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order