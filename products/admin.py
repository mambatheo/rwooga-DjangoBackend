from django.contrib import admin
from .models import ServiceCategory, Product, ProductMedia, Feedback


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1

class FeedbackInline(admin.TabularInline):
    model = Feedback
    extra = 0
    readonly_fields = ['client_name', 'rating', 'message', 'created_at']


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['display_order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'unit_price', 'published', 'created_at']
    list_filter = ['published', 'category', 'created_at']
    search_fields = ['name', 'short_description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductMediaInline, FeedbackInline]
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'category', 'short_description', 'detailed_description')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'currency')
        }),
        ('Dimensions', {
            'fields': ('length', 'width', 'height', 'measurement_unit', 'material')
        }),
        ('Product Variations', {
            'fields': ('available_sizes', 'available_colors'),
            'description': 'Enter comma-separated values (e.g., Small, Medium, Large)'
        }),
        ('Publishing', {
            'fields': ('published', 'uploaded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    list_display = ['product', 'display_order', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['product__name', 'alt_text']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['product', 'client_name', 'rating', 'published', 'created_at']
    list_filter = ['published', 'rating', 'created_at']
    search_fields = ['client_name', 'message', 'product__name']
    actions = ['make_published', 'make_unpublished']
    
    def make_published(self, request, queryset):
        queryset.update(published=True)
    make_published.short_description = "Publish selected feedback"
    
    def make_unpublished(self, request, queryset):
        queryset.update(published=False)
    make_unpublished.short_description = "Unpublish selected feedback"