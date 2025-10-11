from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Professional admin interface for custom User model"""
    
    list_display = ['username', 'email', 'phone', 'role', 'is_phone_verified', 'is_active', 'created_at']
    list_filter = ['role', 'is_phone_verified', 'is_email_verified', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('phone', 'role', 'is_phone_verified', 'is_email_verified', 'profile_picture', 'address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('phone', 'role', 'email')
        }),
    )