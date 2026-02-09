from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import CustomRequest, ServiceCategory, Product, ProductMedia, Feedback

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
            'pricing_type',
            'is_active', 
            'created_at', 
            'updated_at', 
            'product_count'
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
            'currency', 'length', 'width', 'height', 
            'product_volume', 'measurement_unit', 'available_sizes', 
            'available_colors', 'published', 
            'uploaded_by', 'created_at', 'updated_at', 'media', 
            'average_rating'
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


class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.UUIDField(source='user.id', read_only=True)
    product_name = serializers.ReadOnlyField(source='product.name')
    user_name = serializers.ReadOnlyField(source='user.full_name')

    class Meta:
        model = Feedback
        fields = [
            'id', 'product', 'product_name', 'client_name', 
            'message', 'rating', 'published', 'created_at','user', 'user_name'
        ]
        read_only_fields = ['id', 'published', 'created_at','user']


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
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']