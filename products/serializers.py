from rest_framework import serializers
from .models import ServiceCategory, Product, ProductMedia, Feedback, Discount, ProductDiscount


class ServiceCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
   
    class Meta:
        model = ServiceCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "display_order",
            "created_at",
            "updated_at",
            "product_count",
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
            "material",
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
        if data["length"] <= 0 or data["width"] <= 0 or data["height"] <= 0:
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
    class Meta:
        model = Feedback
        fields = [
            "id",
            "product",
            "client_name",
            "message",
            "rating",
            "published",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


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