from django.urls import path, include
from rest_framework import routers
from accounts.views import UserViewSet, LoginMixin, AuthViewSet, ProfileViewSet

route = routers.DefaultRouter()
route.register('user', UserViewSet, basename='user')
route.register('login', LoginMixin, basename='login')
route.register('auth', AuthViewSet, basename='auth')
route.register('profile', ProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(route.urls)),
]