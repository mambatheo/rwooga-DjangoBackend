
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import *


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    
    list_display = [
        'id',
        'email',
        'get_full_name',
        'phone_number',
        'user_type',
        'is_active',
        'date_joined',
       
    ]
    
    list_filter = [
        'user_type',
        'is_active',
        'is_staff',
        'date_joined'
    ]
    
    search_fields = [
        'email',
        'full_name',      
        'phone_number',
     
    ]
    
    ordering = ['-date_joined']
    
    readonly_fields = [
        'id',
        'date_joined',
        'updated_at',
        
    ]
    
    fieldsets = (
        (_('Authentication'), {
            'fields': ('id', 'email', 'password')
        }),
       
       
        (_('User Classification'), {
            'fields': ('user_type',)
        }),
        (_('Permissions & Status'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
      
        (_('Important Dates'), {
            'fields': ('date_joined', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'full_name',               
                'phone_number',
                'password1',
                'password2',
                'user_type',
                'is_active',
                'is_staff'
            ),
        }),
    )
    
    def get_full_name(self, obj):
       
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
@admin.register(VerificationCode)  
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'code',
        'created_on',
        'user',
        'user_id'
    ]
    
    readonly_fields = [
        'id',        
        'code',
        'created_on',
        'user'
    ]
    
    ordering = [
        'created_on',
    ]
    list_filter = [
        'user',
        'created_on'
    ]
    search_fields = [
        'id',
        'user'
    ]
    
    fieldsets = (
        (None, {
            "fields": (
                'id','code','created_on','user'
            ),
        }),
    )
    




#Customize admin site headers
admin.site.site_header = "Rwooga Administration"
admin.site.site_title = "Rwooga Admin Portal"
admin.site.index_title = "Welcome to Rwooga Admin Portal"
