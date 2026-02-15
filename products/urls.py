from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServiceCategoryViewSet,
    ProductViewSet,
    ProductMediaViewSet,
    FeedbackViewSet,
    CustomRequestViewSet,
    WishlistItemViewSet,
    WishlistViewSet,
    DiscountViewSet,
    ProductDiscountViewSet
)

router = DefaultRouter()
router.register('categories', ServiceCategoryViewSet)
router.register('products', ProductViewSet)
router.register('media', ProductMediaViewSet)
router.register('feedback', FeedbackViewSet)
router.register('custom-requests', CustomRequestViewSet)
router.register('wishlist', WishlistViewSet, basename='wishlist')
router.register('wishlist-items', WishlistItemViewSet, basename='wishlist-item')
router.register('discounts', DiscountViewSet)
router.register('product-discounts', ProductDiscountViewSet)

urlpatterns = [
    path('', include(router.urls)),  
]