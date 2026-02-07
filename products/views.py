from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg
from .models import ServiceCategory, Product, ProductMedia, Feedback, Discount, ProductDiscount
from .serializers import (
    ServiceCategorySerializer,
    ProductSerializer,
    ProductListSerializer,
    ProductMediaSerializer,
    FeedbackSerializer,
    DiscountSerializer,
    ProductDiscountSerializer
)


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().annotate(
        average_rating=Avg("feedbacks__rating")
    )
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'short_description', 'detailed_description']
    ordering_fields = ['unit_price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        published = self.request.query_params.get("published")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")

        if category:
            qs = qs.filter(category_id=category)
        if published is not None:
            qs = qs.filter(published=published.lower() == "true")
        if min_price:
            qs = qs.filter(unit_price__gte=min_price)
        if max_price:
            qs = qs.filter(unit_price__lte=max_price)

        return qs

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        product = self.get_object()
        product.published = True
        product.save()
        return Response({"status": "Product published"})

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        product = self.get_object()
        product.published = False
        product.save()
        return Response({"status": "Product unpublished"})
    
  
class ProductMediaViewSet(viewsets.ModelViewSet):
    queryset = ProductMedia.objects.all()
    serializer_class = ProductMediaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        qs = super().get_queryset()
        product_id = self.request.query_params.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Non-staff users only see published feedback
        if not self.request.user.is_staff:
            qs = qs.filter(published=True)
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs


class DiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ProductDiscountViewSet(viewsets.ModelViewSet):
    queryset = ProductDiscount.objects.all()
    serializer_class = ProductDiscountSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        product_id = self.request.query_params.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs