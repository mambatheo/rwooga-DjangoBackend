from rest_framework import viewsets, permissions, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg
from .models import ServiceCategory, Product, ProductMedia, Feedback, CustomRequest
from .permissions import AnyoneCanCreateRequest, AnyoneCanCreateRequest, IsAdminOrStaffOrReadOnly, IsStaffOnly, CustomerCanCreateFeedback
from .serializers import (
    CustomRequestSerializer,
    CustomRequestSerializer,
    ServiceCategorySerializer,
    ProductSerializer,
    ProductListSerializer,
    ProductMediaSerializer,
    FeedbackSerializer,
)


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().annotate(
        average_rating=Avg("feedbacks__rating")
    )
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
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

    @action(detail=True, methods=["post"], permission_classes=[IsStaffOnly])
    def publish(self, request, pk=None):
        product = self.get_object()
        product.published = True
        product.save()
        return Response({"status": "Product published"})

    @action(detail=True, methods=["post"], permission_classes=[IsStaffOnly])
    def unpublish(self, request, pk=None):
        product = self.get_object()
        product.published = False
        product.save()
        return Response({"status": "Product unpublished"})
    
  


class ProductMediaViewSet(viewsets.ModelViewSet):
    queryset = ProductMedia.objects.all()
    serializer_class = ProductMediaSerializer
    permission_classes = [IsAdminOrStaffOrReadOnly]
    
    def get_queryset(self):
        qs = super().get_queryset()
        product_id = self.request.query_params.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [CustomerCanCreateFeedback]
    authentication_classes = []
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
    
    @action(detail=True, methods=['post'], permission_classes=[IsStaffOnly])
    def moderate(self, request, pk=None):
        """Toggle feedback published status (staff only)"""
        feedback = self.get_object()
        feedback.published = not feedback.published
        feedback.save()
        return Response({
            "published": feedback.published,
            "message": f"Feedback {'published' if feedback.published else 'unpublished'}"
        })

class CustomRequestViewSet(viewsets.ModelViewSet):
    queryset = CustomRequest.objects.all()
    serializer_class = CustomRequestSerializer
    permission_classes = [AnyoneCanCreateRequest]
    
    
    
    @action(detail=True, methods=['post'], permission_classes=[IsStaffOnly])
    def update_status(self, request, pk=None):
        """Update request status (staff only)"""
        custom_request = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['pending', 'in_progress', 'completed', 'cancelled']:
            return Response(
                {"error": "Invalid status"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        custom_request.status = new_status
        custom_request.save()
        
        return Response({
            "status": custom_request.status,
            "message": f"Request status updated to {new_status}"
        })
  

