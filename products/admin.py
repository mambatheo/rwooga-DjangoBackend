from django.contrib import admin
from .models import ServiceCategory, Product, ProductMedia, Feedback, CustomRequest, Wishlist


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1

class FeedbackInline(admin.TabularInline):
    model = Feedback
    extra = 0
    readonly_fields = ['client_name', 'rating', 'message', 'created_at']


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'category', 'unit_price', 'published', 'created_at']
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

@admin.register(CustomRequest)
class CustomRequestAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'title', 'service_category', 'status', 'created_at']
    list_filter = ['status', 'service_category', 'created_at']
    search_fields = ['client_name', 'client_email', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('client_name', 'client_email', 'client_phone')
        }),
        ('Request Details', {
            'fields': ('service_category', 'title', 'description', 'reference_file', 'budget')
        }),
        ('Status & Notes', {
            'fields': ('status',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_in_progress', 'mark_completed', 'mark_cancelled']
    
    def mark_in_progress(self, request, queryset):
        queryset.update(status='IN_PROGRESS')
    mark_in_progress.short_description = "Mark as In Progress"
    
    def mark_completed(self, request, queryset):
        queryset.update(status='COMPLETED')
    mark_completed.short_description = "Mark as Completed"
    
    def mark_cancelled(self, request, queryset):
        queryset.update(status='CANCELLED')
    mark_cancelled.short_description = "Mark as Cancelled"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__full_name', 'user__email', 'product__name']
    readonly_fields = ['created_at']