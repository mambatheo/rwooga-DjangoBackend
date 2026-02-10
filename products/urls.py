from rest_framework.routers import DefaultRouter
from .views import (
    ServiceCategoryViewSet,
    ProductViewSet,
    ProductMediaViewSet,
    FeedbackViewSet,
    CustomRequestViewSet,
    WishlistItemViewSet,
    WishlistViewSet,
)

router = DefaultRouter()
router.register('categories', ServiceCategoryViewSet)
router.register('products', ProductViewSet)
router.register('media', ProductMediaViewSet)
router.register('feedback', FeedbackViewSet)
router.register('custom-requests', CustomRequestViewSet)
router.register('wishlist', WishlistViewSet, basename='wishlist')
router.register('wishlist-items', WishlistItemViewSet, basename='wishlist-item')

urlpatterns = router.urls
