from django.contrib import admin
from .models import ServiceCategory, ServiceProvider, Service, Subscription

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'status', 'average_rating', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['business_name', 'business_email', 'user__username']
    readonly_fields = ['average_rating', 'total_ratings', 'created_at', 'updated_at']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'category', 'base_price', 'is_active', 'current_stock']
    list_filter = ['category', 'pricing_type', 'is_active', 'is_available']
    search_fields = ['name', 'description', 'provider__business_name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['customer', 'service', 'status', 'used_units', 'remaining_units', 'end_date']
    list_filter = ['status', 'auto_renew', 'start_date', 'end_date']
    search_fields = ['customer__username', 'service__name']
    readonly_fields = ['remaining_units', 'created_at', 'updated_at']