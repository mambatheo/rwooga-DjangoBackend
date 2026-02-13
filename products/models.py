import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator

class ServiceCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, blank=True, null=True)
    description = models.TextField()
    
    requires_dimensions = models.BooleanField(
        default=False, 
        help_text="Does this service need length/width/height?"
    )
    requires_material = models.BooleanField(
        default=False, 
        help_text="Does this service need material specification?"
    )
    pricing_type = models.CharField(
        max_length=20,
        choices=[
            ('fixed', 'Fixed Price'),
            ('custom', 'Custom Quote'),
            
        ],
        default='custom'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["name"]
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200, blank=False, null=False)
    slug = models.SlugField(max_length=200, blank=True, null=True)
    short_description = models.CharField(max_length=255, blank=False, null=False)
    detailed_description = models.TextField(max_length=2000, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    currency = models.CharField(max_length=3, default="RWF", blank=True, null=True)
    
    length = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    width = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    height = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
    measurement_unit = models.CharField(max_length=10, default="cm^3", blank=True, null=True)
 
    published = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NEW: Product variations (simple text fields)
    available_sizes = models.CharField(max_length=200, blank=True, help_text="e.g., Small, Medium, Large")
    available_colors = models.CharField(max_length=200, blank=True, help_text="e.g., Red, Blue, Green")
    available_materials = models.CharField(max_length=200, blank=True, help_text="e.g., PLA, ABS, Resin")
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    @property
    def product_volume(self):
        if self.length and self.width and self.height:
            return self.length * self.width * self.height
        return None

    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}

        if self.category:
            # Check if dimensions are required
            if self.category.requires_dimensions:
                if not self.length:
                    errors['length'] = 'Length is required for this service category.'
                if not self.width:
                    errors['width'] = 'Width is required for this service category.'
                if not self.height:
                    errors['height'] = 'Height is required for this service category.'
        
            # Check if material is required
            if self.category.requires_material and not self.material:
                errors['material'] = 'Material is required for this service category.'
        
            # Check pricing based on category pricing type
            if self.category.pricing_type == 'fixed' and not self.unit_price:
                errors['unit_price'] = 'Price is required for fixed-price services.'
        if errors:
            raise ValidationError(errors)
    
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
        verbose_name = "Product Media"
        verbose_name_plural = "Product Media"
    
    def clean(self):
        if not any([self.image, self.video_file, self.video_url, self.model_3d]):
            raise ValidationError('At least one media file (image, video, or 3D model) must be provided.')

    def __str__(self):
        return f"{self.product.name} - Media {self.display_order}"

class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name="feedbacks", on_delete=models.CASCADE)
    client_name = models.CharField(max_length=200)
    message = models.TextField()
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback"

#customer request
class CustomRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    

    client_name = models.CharField(max_length=200)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=20)
    
   
    service_category = models.ForeignKey(
        ServiceCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Optional: What service is this related to?"
    )
    title = models.CharField(max_length=200, help_text="Brief title of what you need")
    description = models.TextField(help_text="Detailed description of your request")
    
    
    reference_file = models.FileField(
    upload_to="custom_requests/", 
    blank=True, 
    null=True,
    validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'stl', 'obj'])],
    help_text="Upload reference images or sketches"
)
    
    budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Your approximate budget in RWF"
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Custom Request"
        verbose_name_plural = "Custom Requests"

    def __str__(self):
        return f"{self.client_name} - {self.title}"

class Wishlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlisted_by")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlists")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']  
        ordering = ['-created_at']
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlists"

    def __str__(self):
        return f"{self.user.full_name} - {self.product.name}"

class WishlistItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlist_items")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['wishlist', 'product']
        ordering = ['-created_at']
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"

    def __str__(self):
        return f"{self.wishlist.user.full_name} - {self.product.name}"