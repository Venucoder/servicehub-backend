# backend/apps/services/admin.py
from django.contrib import admin
from .models import (
    ServiceCategory, 
    ServiceProvider, 
    Service, 
    PrepaidCardOption,
    PrepaidCard,
    CardUsage
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
        'is_active', 
        'current_stock',
        'supports_prepaid_cards',
        'supports_immediate_delivery'
    ]
    list_filter = [
        'category', 
        'is_active', 
        'is_available',
        'supports_prepaid_cards',
        'supports_immediate_delivery'
    ]
    search_fields = ['name', 'description', 'provider__business_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('provider', 'category', 'name', 'description')
        }),
        ('Pricing', {
            'fields': ('base_price', 'unit', 'quantity_options', 'minimum_order')
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
        ('Features', {
            'fields': (
                'supports_immediate_delivery', 
                'immediate_delivery_time',
                'supports_prepaid_cards'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PrepaidCardOption)
class PrepaidCardOptionAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'service',
        'total_units',
        'price',
        'price_per_unit',
        'savings',
        'is_active',
        'display_order'
    ]
    list_filter = ['is_active', 'service__category']
    search_fields = ['name', 'service__name']
    readonly_fields = ['price_per_unit', 'savings', 'created_at', 'updated_at']
    ordering = ['service', 'display_order', 'total_units']


@admin.register(PrepaidCard)
class PrepaidCardAdmin(admin.ModelAdmin):
    list_display = [
        'customer',
        'get_service_name',
        'status',
        'used_units',
        'remaining_units',
        'purchased_at',
        'last_used_at'
    ]
    list_filter = [
        'status',
        'purchased_at'
    ]
    search_fields = [
        'customer__username',
        'customer__email',
        'card_option__service__name'
    ]
    readonly_fields = [
        'remaining_units',
        'purchased_at',
        'last_used_at',
        'exhausted_at',
        'cancelled_at'
    ]
    
    fieldsets = (
        ('Card Info', {
            'fields': ('customer', 'card_option', 'status')
        }),
        ('Unit Tracking', {
            'fields': ('total_units', 'used_units', 'remaining_units')
        }),
        ('Pricing', {
            'fields': ('total_amount', 'per_unit_price')
        }),
        ('Timestamps', {
            'fields': (
                'purchased_at',
                'last_used_at',
                'exhausted_at',
                'cancelled_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_service_name(self, obj):
        """Display service name from card option"""
        return obj.card_option.service.name
    get_service_name.short_description = 'Service'
    get_service_name.admin_order_field = 'card_option__service__name'


@admin.register(CardUsage)
class CardUsageAdmin(admin.ModelAdmin):
    list_display = [
        'card',
        'get_customer_name',
        'units_used',
        'marked_by',
        'used_at'
    ]
    list_filter = ['used_at']
    search_fields = [
        'card__customer__username',
        'card__card_option__service__name'
    ]
    readonly_fields = ['used_at']
    
    fieldsets = (
        ('Usage Info', {
            'fields': ('card', 'units_used', 'marked_by', 'notes')
        }),
        ('Timestamp', {
            'fields': ('used_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_customer_name(self, obj):
        """Display customer name"""
        return obj.card.customer.username
    get_customer_name.short_description = 'Customer'
    get_customer_name.admin_order_field = 'card__customer__username'