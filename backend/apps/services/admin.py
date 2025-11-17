from django.contrib import admin
from .models import (
    ServiceCategory, 
    ServiceProvider, 
    Service, 
    SubscriptionPackage,
    Subscription,
    SubscriptionUsage
)

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
    list_display = [
        'name', 
        'provider', 
        'category', 
        'base_price', 
        'pricing_type',
        'is_active', 
        'current_stock',
        'supports_immediate_delivery'
    ]
    list_filter = [
        'category', 
        'pricing_type', 
        'is_active', 
        'is_available',
        'supports_immediate_delivery'
    ]
    search_fields = ['name', 'description', 'provider__business_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('provider', 'category', 'name', 'description')
        }),
        ('Pricing', {
            'fields': ('pricing_type', 'base_price', 'unit', 'minimum_order')
        }),
        ('Availability', {
            'fields': ('is_active', 'is_available', 'has_stock_tracking', 'current_stock')
        }),
        ('Business Hours', {
            'fields': (
                'business_hours_start', 
                'business_hours_end', 
                'operating_days'
            )
        }),
        ('Delivery Options', {
            'fields': ('supports_immediate_delivery', 'immediate_delivery_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SubscriptionPackage)
class SubscriptionPackageAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'service',
        'units',
        'price',
        'price_per_unit',
        'savings',
        'is_active',
        'display_order'
    ]
    list_filter = ['is_active', 'service__category']
    search_fields = ['name', 'service__name']
    readonly_fields = ['price_per_unit', 'savings', 'created_at', 'updated_at']
    ordering = ['service', 'display_order', 'units']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'customer',
        'get_service_name',
        'status',
        'delivery_type',
        'used_units',
        'remaining_units',
        'created_at'
    ]
    list_filter = [
        'status',
        'delivery_type',
        'created_at'
    ]
    search_fields = [
        'customer__username',
        'customer__email',
        'package__service__name'
    ]
    readonly_fields = [
        'remaining_units',
        'created_at',
        'updated_at',
        'paused_at',
        'completed_at',
        'cancelled_at'
    ]
    
    fieldsets = (
        ('Subscription Info', {
            'fields': ('customer', 'package', 'status', 'delivery_type')
        }),
        ('Unit Tracking', {
            'fields': ('total_units', 'used_units', 'remaining_units')
        }),
        ('Pricing', {
            'fields': ('total_amount', 'per_unit_price')
        }),
        ('Delivery Settings', {
            'fields': (
                'delivery_address',
                'preferred_time',
                'delivery_days',
                'units_per_delivery'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'paused_at',
                'completed_at',
                'cancelled_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_service_name(self, obj):
        """Display service name from package"""
        return obj.package.service.name
    get_service_name.short_description = 'Service'
    get_service_name.admin_order_field = 'package__service__name'


@admin.register(SubscriptionUsage)
class SubscriptionUsageAdmin(admin.ModelAdmin):
    list_display = [
        'subscription',
        'get_customer_name',
        'units_used',
        'usage_type',
        'created_at'
    ]
    list_filter = ['usage_type', 'created_at']
    search_fields = [
        'subscription__customer__username',
        'subscription__package__service__name'
    ]
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Usage Info', {
            'fields': ('subscription', 'units_used', 'usage_type', 'notes')
        }),
        ('Pickup Details', {
            'fields': ('picked_up_at',),
            'classes': ('collapse',)
        }),
        ('Delivery Details', {
            'fields': ('delivered_at', 'delivered_by'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_customer_name(self, obj):
        """Display customer name"""
        return obj.subscription.customer.username
    get_customer_name.short_description = 'Customer'
    get_customer_name.admin_order_field = 'subscription__customer__username'