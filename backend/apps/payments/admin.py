# backend/apps/payments/admin.py
from django.contrib import admin
from .models import Payment, Wallet, WalletTransaction, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id', 
        'customer', 
        'get_payment_for',
        'amount', 
        'payment_method', 
        'status', 
        'created_at'
    ]
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = [
        'transaction_id', 
        'gateway_transaction_id', 
        'customer__username',
        'order__order_number',
        'prepaid_card__card_option__service__name'
    ]
    readonly_fields = ['transaction_id', 'created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('transaction_id', 'customer', 'amount', 'payment_method', 'status')
        }),
        ('Related Items', {
            'fields': ('order', 'prepaid_card')
        }),
        ('Gateway Details', {
            'fields': ('gateway_name', 'gateway_transaction_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_payment_for(self, obj):
        """Display what this payment is for"""
        if obj.order:
            return f"Order: {obj.order.order_number}"
        elif obj.prepaid_card:
            service_name = obj.prepaid_card.card_option.service.name
            return f"Prepaid Card: {service_name}"
        return "Unknown"
    get_payment_for.short_description = 'Payment For'


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'is_active', 'updated_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Wallet Information', {
            'fields': ('user', 'balance', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'get_user', 
        'transaction_type', 
        'amount', 
        'balance_after', 
        'created_at'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['wallet__user__username', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('wallet', 'transaction_type', 'amount', 'balance_after')
        }),
        ('Details', {
            'fields': ('description', 'payment')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_user(self, obj):
        """Display wallet owner"""
        return obj.wallet.user.username
    get_user.short_description = 'User'
    get_user.admin_order_field = 'wallet__user__username'


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = [
        'get_payment_id', 
        'get_customer', 
        'amount', 
        'status', 
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['payment__transaction_id', 'payment__customer__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('Refund Information', {
            'fields': ('payment', 'amount', 'reason', 'status')
        }),
        ('Processing', {
            'fields': ('processed_by', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_payment_id(self, obj):
        """Display payment transaction ID"""
        return obj.payment.transaction_id
    get_payment_id.short_description = 'Payment ID'
    get_payment_id.admin_order_field = 'payment__transaction_id'
    
    def get_customer(self, obj):
        """Display customer name"""
        return obj.payment.customer.username
    get_customer.short_description = 'Customer'
    get_customer.admin_order_field = 'payment__customer__username'