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
        # User history: filter by the logged-in user
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user) 
        

    def perform_create(self, serializer):
        # Automatically link the order to the logged-in user
        serializer.save(user=self.request.user)