from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Order, OrderItem, OrderDiscount, Return, Refund, Shipping
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    OrderItemSerializer,
    OrderDiscountSerializer,
    ShippingSerializer,
    ReturnSerializer,
    ReturnApproveSerializer,
    ReturnRejectSerializer,
    RefundSerializer,
    RefundCompleteSerializer,
)


class IsAdminOrStaff(permissions.BasePermission):
    """Allow access only to admin or staff users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or getattr(request.user, 'is_admin', False)
        )


class ShippingViewSet(viewsets.ReadOnlyModelViewSet):
    
    serializer_class = ShippingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['district', 'sector', 'street_address', 'shipping_phone']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Shipping.objects.none()
        if not self.request.user.is_authenticated:
            return Shipping.objects.none()

        user = self.request.user

        # Admin/staff see all shipping addresses
        if user.is_staff or getattr(user, 'is_admin', False):
            return Shipping.objects.all()

        # Regular users see only shipping addresses from their own orders
        return Shipping.objects.filter(orders__user=user).distinct()


class OrderViewSet(viewsets.ModelViewSet):
 
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = [
        'order_number',
        'shipping_address__district',
        'shipping_address__sector',
        'shipping_address__street_address'
    ]
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        if self.action == 'list':
            return OrderListSerializer
        if self.action in ('update', 'partial_update'):
            return OrderUpdateSerializer
        return OrderSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        if not self.request.user.is_authenticated:
            return Order.objects.none()
        
        # Admin/staff see all orders
        if self.request.user.is_staff or getattr(self.request.user, 'is_admin', False):
            return Order.objects.all().select_related(
                'user', 'shipping_address'
            ).prefetch_related('items', 'order_discounts')
        
        # Regular users see only their own orders
        return Order.objects.filter(user=self.request.user).select_related(
            'shipping_address'
        ).prefetch_related('items', 'order_discounts')

    def get_permissions(self):
        if self.action in ('update', 'partial_update'):
            return [IsAdminOrStaff()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a PENDING order. Only the order owner can cancel."""
        order = self.get_object()

        # Only the owner can cancel
        if order.user != request.user and not (request.user.is_staff or getattr(request.user, 'is_admin', False)):
            return Response(
                {'error': 'You do not have permission to cancel this order.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if order.status != 'PENDING':
            return Response(
                {'error': f'Cannot cancel an order with status "{order.get_status_display()}". Only PENDING orders can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = 'CANCELLED'
        order.save()
        return Response(OrderSerializer(order, context={'request': request}).data)


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return OrderItem.objects.none()

        user = self.request.user
        qs = OrderItem.objects.select_related('order', 'product')

        # Admin/staff see all
        if not (user.is_staff or getattr(user, 'is_admin', False)):
            qs = qs.filter(order__user=user)

        # Optional filter by order
        order_id = self.request.query_params.get('order')
        if order_id:
            qs = qs.filter(order_id=order_id)

        return qs


class OrderDiscountViewSet(viewsets.ReadOnlyModelViewSet):
    
    serializer_class = OrderDiscountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return OrderDiscount.objects.none()

        user = self.request.user
        qs = OrderDiscount.objects.select_related('order', 'discount')

        if not (user.is_staff or getattr(user, 'is_admin', False)):
            qs = qs.filter(order__user=user)

        order_id = self.request.query_params.get('order')
        if order_id:
            qs = qs.filter(order_id=order_id)

        return qs


class ReturnViewSet(viewsets.ModelViewSet):
 
    serializer_class = ReturnSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['return_number', 'reason', 'detailed_reason']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Return.objects.none()
        if not self.request.user.is_authenticated:
            return Return.objects.none()

        user = self.request.user

        # Admin/staff see all returns
        if user.is_staff or getattr(user, 'is_admin', False):
            return Return.objects.all().select_related('order', 'user')

        # Regular users see only their own returns
        return Return.objects.filter(user=user).select_related('order')

    def get_permissions(self):
        if self.action in ('approve', 'reject', 'complete'):
            return [IsAdminOrStaff()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a return request. Admin/staff only."""
        return_obj = self.get_object()

        if return_obj.status != 'REQUESTED':
            return Response(
                {'error': f'Cannot approve a return with status "{return_obj.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReturnApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_amount = serializer.validated_data.get('approved_refund_amount')
        return_obj.approve(amount=approved_amount)

        return Response(ReturnSerializer(return_obj, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a return request with a reason. Admin/staff only."""
        return_obj = self.get_object()

        if return_obj.status != 'REQUESTED':
            return Response(
                {'error': f'Cannot reject a return with status "{return_obj.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReturnRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return_obj.reject(reason=serializer.validated_data['rejection_reason'])

        return Response(ReturnSerializer(return_obj, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a return as completed. Admin/staff only."""
        return_obj = self.get_object()

        if return_obj.status != 'APPROVED':
            return Response(
                {'error': f'Cannot complete a return with status "{return_obj.get_status_display()}". Only APPROVED returns can be completed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return_obj.status = 'COMPLETED'
        return_obj.save()

        return Response(ReturnSerializer(return_obj, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def cancel_return(self, request, pk=None):
        """Cancel a return request. Only the owner can cancel their own REQUESTED return."""
        return_obj = self.get_object()

        if return_obj.user != request.user and not (request.user.is_staff or getattr(request.user, 'is_admin', False)):
            return Response(
                {'error': 'You do not have permission to cancel this return.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if return_obj.status != 'REQUESTED':
            return Response(
                {'error': f'Cannot cancel a return with status "{return_obj.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return_obj.status = 'CANCELLED'
        return_obj.save()

        return Response(ReturnSerializer(return_obj, context={'request': request}).data)


class RefundViewSet(viewsets.ModelViewSet):
   
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['refund_number', 'reason']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Refund.objects.none()
        if not self.request.user.is_authenticated:
            return Refund.objects.none()

        user = self.request.user

        # Admin/staff see all refunds
        if user.is_staff or getattr(user, 'is_admin', False):
            return Refund.objects.all().select_related('order', 'user')

        # Regular users see only their own refunds
        return Refund.objects.filter(user=user).select_related('order')

    def get_permissions(self):
        if self.action in ('complete', 'fail'):
            return [IsAdminOrStaff()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark refund as completed. Admin/staff only."""
        refund = self.get_object()

        if refund.status != 'PENDING':
            return Response(
                {'error': f'Cannot complete a refund with status "{refund.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RefundCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transaction_id = serializer.validated_data.get('transaction_id', '')
        refund.mark_completed(transaction_id=transaction_id or None)

        return Response(RefundSerializer(refund, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """Mark a refund as failed. Admin/staff only."""
        refund = self.get_object()

        if refund.status != 'PENDING':
            return Response(
                {'error': f'Cannot fail a refund with status "{refund.get_status_display()}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refund.status = 'FAILED'
        refund.save()

        return Response(RefundSerializer(refund, context={'request': request}).data)