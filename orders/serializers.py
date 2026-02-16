from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from .models import Order, OrderItem, OrderDiscount, Return, Refund, Shipping
from products.models import Product, Discount

class  ShippingSerializer(serializers.ModelSerializer):
    shipping_fee = serializers.CharField(read_only=True)
    shipping_telephone = serializers.CharField(max_length=10, read_only=True)
    district = serializers.CharField(read_only=True)
    sector = serializers.CharField(read_only=True)
    street_address = serializers.CharField(read_only=True)
    
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_thumbnail = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    quantity_available_for_return = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'product_slug',
            'product_thumbnail',
            'quantity',
            'price_at_purchase',
            'subtotal',
            'quantity_returned',
            'refunded_amount',
            'quantity_available_for_return',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'product_name',
            'subtotal',
            'quantity_returned',
            'refunded_amount',
            'quantity_available_for_return',
            'created_at',
            'updated_at',
        ]
    
    def get_product_thumbnail(self, obj):
        first_media = obj.product.media.first()
        if first_media and first_media.image:
            return self.context['request'].build_absolute_uri(first_media.image.url)
        return None


class OrderItemCreateSerializer(serializers.Serializer):
    """Simplified serializer for creating order items"""
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(published=True))
    quantity = serializers.IntegerField(min_value=1)
    
    def validate_product(self, value):
        if not value.published:
            raise serializers.ValidationError("This product is not available for purchase.")
        return value


class OrderDiscountSerializer(serializers.ModelSerializer):
    discount_name = serializers.CharField(source='discount.name', read_only=True)
    discount_value = serializers.DecimalField(
        source='discount.discount_value',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    discount_type = serializers.CharField(source='discount.discount_type', read_only=True)
    
    class Meta:
        model = OrderDiscount
        fields = [
            'id',
            'discount',
            'discount_name',
            'discount_value',
            'discount_type',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for order lists"""
    item_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    final_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'total_amount',
            'final_amount',
            'status',
            'status_display',
            'item_count',
            'created_at',
            'paid_at',
            'delivered_at',
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()


class OrderSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual order retrieval"""
    items = OrderItemSerializer(many=True, read_only=True)
    order_discounts = OrderDiscountSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    final_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    can_be_returned = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'user',
            'user_name',
            'user_email',
            'total_amount',
            'shipping_fee',
            'discount_amount',
            'tax_amount',
            'refunded_amount',
            'final_amount',          
            'shipping_fee',
            'tracking_number',
            'customer_notes',
            'status',
            'status_display',
            'can_be_returned',
            'items',
            'order_discounts',
            'created_at',
            'updated_at',
            'paid_at',
            'shipped_at',
            'delivered_at',
        ]
        read_only_fields = [
            'id',
            'order_number',
            'user',
            'total_amount',
            'discount_amount',
            'tax_amount',
            'refunded_amount',
            'final_amount',
            'status',
            'created_at',
            'updated_at',
            'paid_at',
            'shipped_at',
            'delivered_at',
        ]


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating new orders"""
    items = OrderItemCreateSerializer(many=True, write_only=True)
    shipping_address = serializers.CharField()
    shipping_phone = serializers.CharField(max_length=20)
    customer_notes = serializers.CharField(required=False, allow_blank=True)
    shipping_fee = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_code = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item.")
        if len(value) > 50:
            raise serializers.ValidationError("Maximum 50 items per order.")
        return value
    
    def validate_shipping_fee(self, value):
        if value < 0:
            raise serializers.ValidationError("Shipping fee cannot be negative.")
        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        discount_code = validated_data.pop('discount_code', None)
        user = self.context['request'].user
        
        # Calculate subtotal
        subtotal = Decimal('0.00')
        order_items = []
        
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            # Get final price (with product-level discounts if applicable)
            price = product.unit_price
            active_product_discounts = product.product_discounts.filter(is_valid=True)
            if active_product_discounts.exists():
                discount = active_product_discounts.first().discount
                if discount.discount_type == 'percentage':
                    price = price * (1 - discount.discount_value / 100)
                elif discount.discount_type == 'fixed':
                    price = max(price - discount.discount_value, Decimal('0.00'))
            
            subtotal += price * quantity
            order_items.append({
                'product': product,
                'product_name': product.name,
                'quantity': quantity,
                'price_at_purchase': price,
            })
        
        # Apply order-level discount if provided
        discount_amount = Decimal('0.00')
        discount_obj = None
        
        if discount_code:
            try:
                discount_obj = Discount.objects.get(
                    name__iexact=discount_code,
                    is_active=True,
                    start_date__lte=timezone.now(),
                    end_date__gte=timezone.now()
                )
                if discount_obj.discount_type == 'percentage':
                    discount_amount = subtotal * (discount_obj.discount_value / 100)
                elif discount_obj.discount_type == 'fixed':
                    discount_amount = min(discount_obj.discount_value, subtotal)
            except Discount.DoesNotExist:
                raise serializers.ValidationError({"discount_code": "Invalid or expired discount code."})
        
        # Calculate total
        shipping_fee = validated_data.get('shipping_fee', Decimal('0.00'))
        tax_amount = Decimal('0.00')  # Calculate tax if needed
        total_amount = subtotal + shipping_fee + tax_amount - discount_amount
        
        # Create order
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            shipping_fee=shipping_fee,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            shipping_address=validated_data['shipping_address'],
            shipping_phone=validated_data['shipping_phone'],
            customer_notes=validated_data.get('customer_notes', ''),
        )
        
        # Create order items
        for item_data in order_items:
            OrderItem.objects.create(order=order, **item_data)
        
        # Create order discount if applied
        if discount_obj:
            OrderDiscount.objects.create(order=order, discount=discount_obj)
        
        return order
    
    def to_representation(self, instance):
        return OrderSerializer(instance, context=self.context).data


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order details (admin only)"""
    
    class Meta:
        model = Order
        fields = [
            'status',
            'tracking_number',
            'shipped_at',
            'delivered_at',
        ]
    
    def update(self, instance, validated_data):
        status = validated_data.get('status')
        
        # Auto-set timestamps based on status changes
        if status == 'PAID' and not instance.paid_at:
            instance.paid_at = timezone.now()
        elif status == 'SHIPPED' and not instance.shipped_at:
            instance.shipped_at = timezone.now()
        elif status == 'DELIVERED' and not instance.delivered_at:
            instance.delivered_at = timezone.now()
        
        return super().update(instance, validated_data)


class ReturnSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Return
        fields = [
            'id',
            'return_number',
            'order',
            'order_number',
            'user',
            'user_name',
            'reason',
            'detailed_reason',
            'rejection_reason',
            'status',
            'status_display',
            'is_active',
            'requested_refund_amount',
            'approved_refund_amount',
            'created_at',
            'approved_at',
        ]
        read_only_fields = [
            'id',
            'return_number',
            'user',
            'status',
            'rejection_reason',
            'approved_refund_amount',
            'created_at',
            'approved_at',
        ]
    
    def validate_order(self, value):
        user = self.context['request'].user
        
        # Check ownership
        if value.user != user:
            raise serializers.ValidationError("You can only request returns for your own orders.")
        
        # Check if order is eligible for return
        if not value.can_be_returned:
            raise serializers.ValidationError(
                "This order is not eligible for return. Orders can only be returned within 30 days of delivery."
            )
        
        # Check if there's already an active return for this order
        active_returns = Return.objects.filter(
            order=value,
            status__in=['REQUESTED', 'APPROVED']
        )
        if active_returns.exists():
            raise serializers.ValidationError("There is already an active return request for this order.")
        
        return value
    
    def validate_requested_refund_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Refund amount must be greater than zero.")
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReturnApproveSerializer(serializers.Serializer):
    """Serializer for approving returns (admin only)"""
    approved_refund_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    
    def validate_approved_refund_amount(self, value):
        if value and value <= 0:
            raise serializers.ValidationError("Approved refund amount must be greater than zero.")
        return value


class ReturnRejectSerializer(serializers.Serializer):
    """Serializer for rejecting returns (admin only)"""
    rejection_reason = serializers.CharField(required=True)
    
    def validate_rejection_reason(self, value):
        if not value.strip():
            raise serializers.ValidationError("Rejection reason is required.")
        return value


class RefundSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            'id',
            'refund_number',
            'order',
            'order_number',
            'user',
            'user_name',
            'amount',
            'status',
            'status_display',
            'transaction_id',
            'reason',
            'created_at',
            'completed_at',
        ]
        read_only_fields = [
            'id',
            'refund_number',
            'user',
            'status',
            'transaction_id',
            'created_at',
            'completed_at',
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Refund amount must be greater than zero.")
        return value
    
    def validate_order(self, value):
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("You can only request refunds for your own orders.")
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RefundCompleteSerializer(serializers.Serializer):
    """Serializer for completing refunds (admin only)"""
    transaction_id = serializers.CharField(required=False, allow_blank=True)