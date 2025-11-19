# backend/apps/payments/serializers.py
from rest_framework import serializers
from .models import Payment, Wallet, WalletTransaction, Refund
from apps.users.serializers import UserSerializer
from apps.orders.serializers import OrderListSerializer
from apps.services.serializers import PrepaidCardListSerializer


# ============================================
# Payment Serializers
# ============================================

class PaymentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for payment listings"""
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_id', 'customer_name', 'amount',
            'payment_method', 'status', 'created_at'
        ]


class PaymentSerializer(serializers.ModelSerializer):
    """Full serializer for Payments"""
    customer = UserSerializer(read_only=True)
    order = OrderListSerializer(read_only=True)
    prepaid_card = PrepaidCardListSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_id', 'customer', 'order', 'prepaid_card',
            'amount', 'payment_method', 'status', 'gateway_name',
            'gateway_transaction_id', 'notes', 'created_at',
            'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'customer', 'created_at',
            'updated_at', 'completed_at'
        ]


class CreatePaymentSerializer(serializers.ModelSerializer):
    """Serializer for creating payments"""
    
    class Meta:
        model = Payment
        fields = [
            'order_id', 'prepaid_card_id', 'payment_method', 'notes'
        ]
    
    order_id = serializers.UUIDField(required=False, allow_null=True)
    prepaid_card_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate payment creation - must have either order or prepaid_card"""
        order_id = attrs.get('order_id')
        prepaid_card_id = attrs.get('prepaid_card_id')
        
        if not order_id and not prepaid_card_id:
            raise serializers.ValidationError(
                "Payment must be for either an order or a prepaid card"
            )
        
        if order_id and prepaid_card_id:
            raise serializers.ValidationError(
                "Payment cannot be for both an order and a prepaid card"
            )
        
        return attrs


# ============================================
# Wallet Serializers
# ============================================

class WalletSerializer(serializers.ModelSerializer):
    """Serializer for Wallet"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'balance', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'balance', 'created_at', 'updated_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for Wallet Transactions"""
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'wallet', 'transaction_type', 'amount',
            'balance_after', 'description', 'payment', 'created_at'
        ]
        read_only_fields = ['id', 'balance_after', 'created_at']


# ============================================
# Refund Serializers
# ============================================

class RefundSerializer(serializers.ModelSerializer):
    """Serializer for Refunds"""
    payment = PaymentListSerializer(read_only=True)
    payment_id = serializers.UUIDField(write_only=True)
    processed_by_name = serializers.CharField(
        source='processed_by.username',
        read_only=True
    )
    
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'payment_id', 'amount', 'reason', 'status',
            'processed_by', 'processed_by_name', 'admin_notes',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'status', 'processed_by', 'created_at',
            'updated_at', 'completed_at'
        ]


class CreateRefundSerializer(serializers.ModelSerializer):
    """Serializer for creating refund requests"""
    
    class Meta:
        model = Refund
        fields = ['payment_id', 'amount', 'reason']
    
    payment_id = serializers.UUIDField()
    
    def validate_payment_id(self, value):
        """Validate payment exists and is refundable"""
        try:
            payment = Payment.objects.get(id=value)
            if payment.status != 'completed':
                raise serializers.ValidationError(
                    "Only completed payments can be refunded"
                )
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found")