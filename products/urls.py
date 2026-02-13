from rest_framework.routers import DefaultRouter
from .views import (
    ServiceCategoryViewSet,
    ProductViewSet,
    ProductMediaViewSet,
    FeedbackViewSet,
    DiscountViewSet,
    ProductDiscountViewSet
)

router = DefaultRouter()
router.register('categories', ServiceCategoryViewSet)
router.register('products', ProductViewSet)
router.register('media', ProductMediaViewSet)
router.register('feedback', FeedbackViewSet)
router.register('discounts', DiscountViewSet)
router.register('product-discounts', ProductDiscountViewSet)

urlpatterns = router.urls
