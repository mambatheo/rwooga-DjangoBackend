import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.text import slugify

class ServiceCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    #icon = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    short_description = models.CharField(max_length=255)
    detailed_description = models.TextField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default="RWF")
    material = models.CharField(max_length=100, blank=True)

    length = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    width = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    height = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])

    product_volume = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    measurement_unit = models.CharField(max_length=10, default="cm")
    

    published = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NEW: Product variations (simple text fields)
    available_sizes = models.CharField(max_length=200, blank=True, help_text="e.g., Small, Medium, Large")
    available_colors = models.CharField(max_length=200, blank=True, help_text="e.g., Red, Blue, Green")
    available_materials = models.CharField(max_length=200, blank=True, help_text="e.g., PLA, ABS, Resin")
    

    @property
    def product_volume(self):
        return self.length * self.width * self.height

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


def validate_image_size(file):
    limit_mb = 110
    if file.size > limit_mb * 1024 * 1024:
        raise ValidationError(f'Max file size is {limit_mb}MB')

def validate_video_size(file):
    limit_mb = 500
    if file.size > limit_mb * 1024 * 1024:
        raise ValidationError(f'Max file size is {limit_mb}MB')

class ProductMedia(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name="media", on_delete=models.CASCADE)
    
    model_3d = models.FileField(upload_to="products/models/", blank=True, null=True)
    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    video_url = models.URLField(max_length=200, blank=True)

    image = models.ImageField(
        upload_to="products/images/", 
        blank=True, 
        null=True,
        validators=[validate_image_size]
    )
    video_file = models.FileField(
        upload_to="products/videos/", 
        blank=True, 
        null=True,
        validators=[validate_video_size]
    )

    class Meta:
        ordering = ['display_order']
    


class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name="feedbacks", on_delete=models.CASCADE)
    client_name = models.CharField(max_length=200)
    message = models.TextField()
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks")

