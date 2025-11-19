# backend/apps/orders/admin.py
from django.contrib import admin
from .models import Order, OrderStatusHistory


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 
        'customer', 
        'service', 
        'status', 
        'delivery_type',
        'quantity',
        'quantity_label',
        'total_amount', 
        'created_at'
    ]
    list_filter = ['status', 'delivery_type', 'created_at']
    search_fields = ['order_number', 'customer__username', 'service__name']
    readonly_fields = [
        'order_number', 
        'expected_delivery_time',
        'created_at', 
        'updated_at',
        'confirmed_at',
        'completed_at',
        'cancelled_at'
    ]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'service', 'status')
        }),
        ('Quantity & Pricing', {
            'fields': ('quantity', 'quantity_label', 'unit_price', 'total_amount')
        }),
        ('Delivery Details', {
            'fields': (
                'delivery_type',
                'delivery_address',
                'scheduled_date',
                'scheduled_time',
                'expected_delivery_time'
            )
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'confirmed_at',
                'completed_at',
                'cancelled_at'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'from_status', 'to_status', 'changed_by', 'created_at']
    list_filter = ['to_status', 'created_at']
    search_fields = ['order__order_number']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Status Change', {
            'fields': ('order', 'from_status', 'to_status', 'changed_by')
        }),
        ('Details', {
            'fields': ('notes', 'created_at')
        }),
    )