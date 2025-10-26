from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'service', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'order_type', 'created_at']
    search_fields = ['order_number', 'customer__username', 'service__name']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'service', 'quantity', 'unit_price', 'total_price']
    
@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'from_status', 'to_status', 'changed_by', 'created_at']
    list_filter = ['to_status', 'created_at']