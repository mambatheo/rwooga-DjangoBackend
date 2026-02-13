from django.urls import path, include
from rest_framework import routers
from accounts.views import UserViewSet, AuthViewSet, ProfileViewSet

router = routers.DefaultRouter()
router.register('user', UserViewSet, basename='user')
router.register('auth', AuthViewSet, basename='auth')
router.register('profile', ProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
]