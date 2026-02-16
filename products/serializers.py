from rest_framework import serializers
from .models import CustomRequest, ServiceCategory, Product, ProductMedia, Feedback, Wishlist, WishlistItem, Discount, ProductDiscount



class ServiceCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
   
    class Meta:
        model = ServiceCategory
        fields = [
            'id', 
            'name', 
            'slug', 
            'description', 
            'requires_dimensions',
            'requires_material',           
            'is_active', 
            'created_at', 
            'updated_at', 
            'product_count'
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at", "product_count"]
    
    def get_product_count(self, obj) -> int:
        return obj.products.count()


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = [
            "id",
            "product",
            "model_3d",
            "image",
            "video_file",
            "video_url",
            "alt_text",
            "display_order",
            "uploaded_at",
        ]
        read_only_fields = ["id", "uploaded_at"]


class ProductSerializer(serializers.ModelSerializer):
    media = ProductMediaSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    final_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "slug",
            "short_description",
            "detailed_description",
            "unit_price",
            "currency",
            "length",
            "width",
            "height",
            "product_volume",
            "measurement_unit",
            "published",
            "uploaded_by",
            "created_at",
            "updated_at",
            "available_sizes",
            "available_colors",
            "available_materials",
            "final_price",
            "media",
            "average_rating",
        ]
        read_only_fields = [
            "id",
            "slug",
            "product_volume",
            "created_at",
            "updated_at",
            "final_price",
            "average_rating",
        ]

    def validate(self, data):
        category = data.get('category') or (self.instance.category if self.instance else None)

        if category:

            # Only validate dimensions if category requires them
            if category.requires_dimensions:
                length = data.get("length")
                width = data.get("width")
                height = data.get("height")

                if not all([length, width, height]):
                    raise serializers.ValidationError(
                        "Length, width, and height are required for this service category."
                    )
                if length <= 0 or width <= 0 or height <= 0:
                    raise serializers.ValidationError(
                        
                "Product dimensions must be greater than zero."
            
                    )        
        return data
    
    def get_final_price(self, obj):
        """
        Calculate final price with discount if available.
        """
        # Try to get the active discount for the product
        active_discounts = obj.product_discounts.filter(is_valid=True)
        if active_discounts.exists():
            discount = active_discounts.first().discount
            if discount.discount_type == 'percentage':
                return obj.unit_price * (1 - discount.discount_value / 100)
            elif discount.discount_type == 'fixed':
                return max(obj.unit_price - discount.discount_value, 0)
        # No discount
        return obj.unit_price


class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.UUIDField(source='user.id', read_only=True)
    product_name = serializers.ReadOnlyField(source='product.name')
    user_name = serializers.ReadOnlyField(source='user.full_name')

    class Meta:
        model = Feedback
        fields = [
            "id",
            "product",
            "product_name",
            "client_name",
            "message",
            "rating",
            "published",
            "created_at",'user', 'user_name'
        ]
        read_only_fields = ['id', 'published', 'created_at','user']


class ProductListSerializer(serializers.ModelSerializer):
    """serializer for product lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    thumbnail = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['id', 'name', 'short_description', 'unit_price',
                  'currency', 'published', 'category_name',
                  'average_rating', 'thumbnail', 'final_price']
 
    def get_thumbnail(self, obj) -> str:
        first_media = obj.media.first()
        if first_media and first_media.image:
            return first_media.image.url
        return None

class CustomRequestSerializer(serializers.ModelSerializer):
    service_category = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(),
        required=False,
        allow_null=True,
        pk_field=serializers.UUIDField()
    )
    service_category_name = serializers.CharField(source='service_category.name', read_only=True)
    
    class Meta:
        model = CustomRequest
        fields = [
            'id', 'client_name', 'client_email', 'client_phone',
            'service_category', 'service_category_name', 'title', 
            'description', 'reference_file', 'budget', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_status(self, value):
        if value not in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
            raise serializers.ValidationError("Invalid status")
        return value
    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_staff:
            status = validated_data.get('status')
            if status:
                instance.status = status
        
        instance.client_name = validated_data.get('client_name', instance.client_name)
        instance.client_email = validated_data.get('client_email', instance.client_email)
        instance.client_phone = validated_data.get('client_phone', instance.client_phone)
        instance.service_category = validated_data.get('service_category', instance.service_category)
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.reference_file = validated_data.get('reference_file', instance.reference_file)
        instance.budget = validated_data.get('budget', instance.budget)

        instance.save()
        return instance


class WishlistItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_price = serializers.ReadOnlyField(source='product.unit_price')
    product_slug = serializers.ReadOnlyField(source='product.slug')
    product_thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = WishlistItem
        fields = [
            'id', 'wishlist', 'product', 'product_name', 
            'product_price', 'product_slug', 'product_thumbnail', 'created_at'
        ]
        read_only_fields = ['id', 'wishlist', 'created_at']
    
   
    def get_product_thumbnail(self, obj) -> str:
        first_media = obj.product.media.first()
        if first_media and first_media.image:
            return first_media.image.url
        return None


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    user_name = serializers.ReadOnlyField(source='user.full_name')
    
    class Meta:
        model = Wishlist
        fields = [
            'id', 'user', 'user_name', 'item_count', 
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']    
    def get_final_price(self, obj):
        """
        Calculate final price with discount if available.
        """
        active_discounts = obj.product_discounts.filter(is_valid=True)
        if active_discounts.exists():
            discount = active_discounts.first().discount
            if discount.discount_type == 'percentage':
                return obj.unit_price * (1 - discount.discount_value / 100)
            elif discount.discount_type == 'fixed':
                return max(obj.unit_price - discount.discount_value, 0)
        # No discount
        return obj.unit_price


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = [
            "id",
            "name",
            "discount_type",
            "discount_value",
            "start_date",
            "end_date",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductDiscountSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    discount_name = serializers.CharField(source='discount.name', read_only=True)
    
    class Meta:
        model = ProductDiscount
        fields = [
            "id",
            "product",
            "product_name",
            "discount_name",
            "discount",
            "is_valid",
            "created_at",
        ]
        read_only_fields = ["id", "created_at","product_name", "discount_name"]