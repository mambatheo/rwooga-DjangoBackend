from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg
from .models import ServiceCategory, Product, ProductMedia, Feedback, CustomRequest, Wishlist, WishlistItem, Discount, ProductDiscount
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
    WishlistItemSerializer,
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
    
    
 
class WishlistViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve user's wishlist
    Use WishlistItemViewSet to add/remove items
    """
    serializer_class = WishlistSerializer
    permission_classes = [IsOwnerOnly]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_wishlist(self, request):
        """Get or create user's wishlist"""
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(wishlist)
        return Response(serializer.data)


class WishlistItemViewSet(viewsets.ModelViewSet):
    """
    Manage wishlist items (add/remove products)
    """
    serializer_class = WishlistItemSerializer
    permission_classes = [IsOwnerOnly]
    
    def get_queryset(self):
        # Get user's wishlist items
        wishlist = Wishlist.objects.filter(user=self.request.user).first()
        if wishlist:
            return WishlistItem.objects.filter(wishlist=wishlist)
        return WishlistItem.objects.none()
    
    def perform_create(self, serializer):
        # Get or create user's wishlist
        wishlist, created = Wishlist.objects.get_or_create(user=self.request.user)
        serializer.save(wishlist=wishlist)
    
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
        
        # Get or create wishlist
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        # Check if item already in wishlist
        wishlist_item = WishlistItem.objects.filter(
            wishlist=wishlist, 
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
            WishlistItem.objects.create(wishlist=wishlist, product=product)
            return Response({
                "message": "Added to wishlist",
                "in_wishlist": True
            }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all items from wishlist"""
        wishlist = Wishlist.objects.filter(user=request.user).first()
        if wishlist:
            count = wishlist.items.count()
            wishlist.items.all().delete()
            return Response({
                "message": f"Removed {count} items from wishlist"
            })
        return Response({"message": "Wishlist is already empty"})


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