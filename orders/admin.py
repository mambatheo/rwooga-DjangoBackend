from django.contrib import admin
from .models import Order, OrderItem, OrderDiscount, Return, Refund, Shipping


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        'id', 'product', 'product_name', 'quantity',
        'price_at_purchase', 'subtotal', 'quantity_returned', 'refunded_amount'
    )
    can_delete = False

    def subtotal(self, obj):
        return obj.subtotal
    subtotal.short_description = 'Subtotal'


class OrderDiscountInline(admin.TabularInline):
    model = OrderDiscount
    extra = 0
    readonly_fields = ('id', 'discount', 'created_at')
    can_delete = False


@admin.register(Shipping)
class ShippingAdmin(admin.ModelAdmin):
    list_display = ('id', 'shipping_fee', 'shipping_phone', 'district', 'sector', 'street_address', 'created_at')
    list_filter = ('district', 'sector', 'created_at')
    search_fields = ('shipping_phone', 'district', 'sector', 'street_address')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'total_amount', 'status', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at', 'paid_at')
    search_fields = (
        'order_number',
        'user__email',
        'user__full_name',
        'shipping_address__shipping_phone',
        'shipping_address__district',
        'shipping_address__sector',
        'shipping_address__street_address'
    )
    readonly_fields = (
        'id', 'order_number', 'user', 'total_amount',
        'discount_amount', 'refunded_amount', 'created_at', 'updated_at', 'paid_at'
    )
    ordering = ('-created_at',)
    inlines = [OrderItemInline, OrderDiscountInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('id', 'order_number', 'user', 'status')
        }),
        ('Amounts', {
            'fields': ('total_amount', 'shipping_fee', 'discount_amount', 'tax_amount', 'refunded_amount')
        }),
        ('Shipping', {
            'fields': ('shipping_address', 'tracking_number', 'customer_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'order', 'quantity', 'price_at_purchase', 'quantity_returned', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product_name', 'order__order_number')
    readonly_fields = ('id', 'order', 'product', 'product_name', 'quantity', 'price_at_purchase', 'created_at', 'updated_at')


@admin.register(OrderDiscount)
class OrderDiscountAdmin(admin.ModelAdmin):
    list_display = ('order', 'discount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('order__order_number',)
    readonly_fields = ('id', 'order', 'discount', 'created_at')


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('return_number', 'order', 'user', 'status', 'requested_refund_amount', 'approved_refund_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('return_number', 'order__order_number', 'user__email', 'user__full_name', 'reason')
    readonly_fields = ('id', 'return_number', 'user', 'created_at', 'approved_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Return Info', {
            'fields': ('id', 'return_number', 'order', 'user', 'status')
        }),
        ('Reason', {
            'fields': ('reason', 'detailed_reason', 'rejection_reason')
        }),
        ('Amounts', {
            'fields': ('requested_refund_amount', 'approved_refund_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'approved_at')
        }),
    )


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('refund_number', 'order', 'user', 'amount', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('refund_number', 'order__order_number', 'user__email', 'user__full_name', 'reason')
    readonly_fields = ('id', 'refund_number', 'user', 'created_at', 'completed_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Refund Info', {
            'fields': ('id', 'refund_number', 'order', 'user', 'status')
        }),
        ('Details', {
            'fields': ('amount', 'reason', 'transaction_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
    )