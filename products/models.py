from django.db import models
from django.utils import timezone
from decimal import Decimal
import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.text import slugify


class ServiceCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
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


# -------------------------
# Product
# -------------------------
class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name="products"
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    short_description = models.CharField(max_length=255)
    detailed_description = models.TextField()

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default="RWF")
    material = models.CharField(max_length=100, blank=True)

    length = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    width = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    height = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])

    product_volume = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    measurement_unit = models.CharField(max_length=10, default="cm")

    published = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    available_sizes = models.CharField(max_length=200, blank=True)
    available_colors = models.CharField(max_length=200, blank=True)
    available_materials = models.CharField(max_length=200, blank=True)

    def save(self, *args, **kwargs):
        # Auto-generate unique slug
        if not self.slug:
            base_slug = slugify(self.name) or str(uuid.uuid4())[:8]
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Auto-calculate volume
        if self.length and self.width and self.height:
            self.product_volume = self.length * self.width * self.height

        super().save(*args, **kwargs)

    def get_final_price(self):
        price = self.unit_price

        for pd in self.product_discounts.select_related("discount"):
            discount = pd.discount
            if pd.is_valid and discount.is_valid():
                if discount.discount_type == Discount.PERCENTAGE:
                    price -= price * (discount.discount_value / Decimal("100"))
                elif discount.discount_type == Discount.FIXED:
                    price -= discount.discount_value

        return max(price, Decimal("0.00"))

    def __str__(self):
        return self.name


# -------------------------
# Validators
# -------------------------
def validate_image_size(file):
    limit_mb = 110
    if file.size > limit_mb * 1024 * 1024:
        raise ValidationError(f"Max file size is {limit_mb}MB")


def validate_video_size(file):
    limit_mb = 500
    if file.size > limit_mb * 1024 * 1024:
        raise ValidationError(f"Max file size is {limit_mb}MB")


# -------------------------
# Product Media
# -------------------------
class ProductMedia(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        related_name="media",
        on_delete=models.CASCADE
    )

    model_3d = models.FileField(upload_to="products/models/", blank=True, null=True)
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
    video_url = models.URLField(blank=True)

    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"Media for {self.product.name}"


# -------------------------
# Feedback
# -------------------------
class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        related_name="feedbacks",
        on_delete=models.CASCADE
    )
    client_name = models.CharField(max_length=200)
    message = models.TextField()
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client_name} - {self.product.name}"


# -------------------------
# Discount
# -------------------------
class Discount(models.Model):
    PERCENTAGE = "percentage"
    FIXED = "fixed"

    DISCOUNT_TYPE_CHOICES = [
        (PERCENTAGE, "Percentage"),
        (FIXED, "Fixed amount"),
    ]

    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    def __str__(self):
        return self.name


# -------------------------
# Product Discount (M2M)
# -------------------------
class ProductDiscount(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_discounts"
    )
    discount = models.ForeignKey(
        Discount,
        on_delete=models.CASCADE,
        related_name="product_discounts"
    )

    is_valid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "discount")

    def __str__(self):
        return f"{self.product.name} - {self.discount.name}"
