from rest_framework import serializers
from .models import ServiceCategory, Product, ProductMedia, Feedback, Discount, ProductDiscount





class ServiceCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceCategory
        fields = "__all__"
    
    def get_product_count(self, obj):
        return obj.products.count()


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    media = ProductMediaSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = "__all__"

    def validate(self, data):
        if data["length"] <= 0 or data["width"] <= 0 or data["height"] <= 0:
            raise serializers.ValidationError("Product dimensions must be greater than zero.")
        return data


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = "__all__"
        read_only_fields = ["published"]


class ProductListSerializer(serializers.ModelSerializer):
    """serializer for product lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'short_description', 'unit_price', 
                  'currency', 'published', 'category_name', 
                  'average_rating', 'thumbnail']
    
    def get_thumbnail(self, obj):
        first_media = obj.media.first()
        if first_media and first_media.image:
            return first_media.image.url
        return None
    

class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = "__all__"


class ProductDiscountSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    discount_name = serializers.CharField(source='discount.name', read_only=True)
    
    class Meta:
        model = ProductDiscount
        fields = "__all__"