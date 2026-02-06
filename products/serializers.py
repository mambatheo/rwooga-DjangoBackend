from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import ServiceCategory, Product, ProductMedia, Feedback

class ServiceCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceCategory
        fields = [
            'id', 'name', 'slug', 'description', 'is_active', 
            'display_order', 'created_at', 'updated_at', 'product_count'
        ]
    
    @extend_schema_field(serializers.IntegerField())
    def get_product_count(self, obj) -> int:
        return obj.products.count()


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = [
            'id', 'product', 'image', 'video_file', 
            'video_url', 'model_3d', 'alt_text', 
            'display_order', 'uploaded_at'
        ]


class ProductSerializer(serializers.ModelSerializer):
    media = ProductMediaSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    product_volume = serializers.FloatField(read_only=True)
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_name', 'name', 'slug', 
            'short_description', 'detailed_description', 'unit_price', 
            'currency', 'material', 'length', 'width', 'height', 
            'product_volume', 'measurement_unit', 'available_sizes', 
            'available_colors', 'published', 
            'uploaded_by', 'created_at', 'updated_at', 'media', 
            'average_rating'
        ]

    def validate(self, data):
        if data["length"] <= 0 or data["width"] <= 0 or data["height"] <= 0:
            raise serializers.ValidationError("Product dimensions must be greater than zero.")
        return data


class FeedbackSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')

    class Meta:
        model = Feedback
        fields = [
            'id', 'product', 'product_name', 'client_name', 
            'message', 'rating', 'published', 'created_at'
        ]
        read_only_fields = ['id', 'published', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    average_rating = serializers.FloatField(read_only=True)
    thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 
            'unit_price', 'currency', 'published', 
            'category_name', 'average_rating', 'thumbnail'
        ]
    
    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_thumbnail(self, obj) -> str:
        first_media = obj.media.first()
        if first_media and first_media.image:
            return first_media.image.url
        return None
