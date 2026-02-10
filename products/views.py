from rest_framework import viewsets, permissions, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg
from .models import ServiceCategory, Product, ProductMedia, Feedback, CustomRequest, Wishlist
from .permissions import AnyoneCanCreateRequest, AnyoneCanCreateRequest, IsAdminOrStaffOrReadOnly, IsOwnerOnly, IsStaffOnly, CustomerCanCreateFeedback
from .serializers import (
    CustomRequestSerializer,
    CustomRequestSerializer,
    ServiceCategorySerializer,
    ProductSerializer,
    ProductListSerializer,
    ProductMediaSerializer,
    FeedbackSerializer,
    WishlistSerializer,
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
        
        if new_status not in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
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
  

class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsOwnerOnly]
    
    def get_queryset(self):
        # Users only see their own wishlist
        return Wishlist.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Add or remove product from wishlist"""
        product_id = request.data.get('product')
        
        if not product_id:
            return Response(
                {"error": "Product ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already in wishlist
        wishlist_item = Wishlist.objects.filter(
            user=request.user, 
            product=product
        ).first()
        
        if wishlist_item:
            # Remove from wishlist
            wishlist_item.delete()
            return Response({
                "message": "Removed from wishlist",
                "in_wishlist": False
            })
        else:
            # Add to wishlist
            Wishlist.objects.create(user=request.user, product=product)
            return Response({
                "message": "Added to wishlist",
                "in_wishlist": True
            }, status=status.HTTP_201_CREATED)