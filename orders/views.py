from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from .models import Order
from .serializers import OrderSerializer

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    # queryset = Order.objects.all().order_by("total_amount")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        if not self.request.user.is_authenticated:
            return Order.objects.none()
    
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically link the order to the logged-in user
        serializer.save(user=self.request.user)