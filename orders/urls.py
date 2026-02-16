from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ShippingViewSet,
    OrderViewSet,
    OrderItemViewSet,
    OrderDiscountViewSet,
    ReturnViewSet,
    RefundViewSet,
)

router = DefaultRouter()

# Register all viewsets
router.register(r'shipping', ShippingViewSet, basename='shipping')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='orderitem')
router.register(r'order-discounts', OrderDiscountViewSet, basename='orderdiscount')
router.register(r'returns', ReturnViewSet, basename='return')
router.register(r'refunds', RefundViewSet, basename='refund')

urlpatterns = [
    path('', include(router.urls)),
]