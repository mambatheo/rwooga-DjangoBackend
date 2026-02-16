from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet,
    OrderItemViewSet,
    OrderDiscountViewSet,
    ReturnViewSet,
    RefundViewSet,
)

router = DefaultRouter()
router.register('orders', OrderViewSet, basename='order')
router.register('order-items', OrderItemViewSet, basename='order-item')
router.register('order-discounts', OrderDiscountViewSet, basename='order-discount')
router.register('returns', ReturnViewSet, basename='return')
router.register('refunds', RefundViewSet, basename='refund')

urlpatterns = [
    path('', include(router.urls)),
]