from rest_framework.routers import DefaultRouter
from .views import (
    ServiceCategoryViewSet,
    ProductViewSet,
    ProductMediaViewSet,
    FeedbackViewSet,
)

router = DefaultRouter()
router.register('categories', ServiceCategoryViewSet)
router.register('products', ProductViewSet)
router.register('media', ProductMediaViewSet)
router.register('feedback', FeedbackViewSet)

urlpatterns = router.urls
