from rest_framework import serializers
from .models import Payment, Wallet, WalletTransaction, Refund
from apps.users.serializers import UserSerializer
from apps.orders.serializers import OrderListSerializer


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payments
    """
    customer = UserSerializer(read_only=True)
    order = OrderListSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_id', 'customer', 'order', 'subscription',
            'amount', 'payment_method', 'status', 'gateway_name',
            'gateway_transaction_id', 'notes', 'created_at',
            'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'customer', 'created_at',
            'updated_at', 'completed_at'
        ]


class CreatePaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for creating payments
    """
    class Meta:
        model = Payment
        fields = [
            'order', 'payment_method', 'notes'
        ]


class WalletSerializer(serializers.ModelSerializer):
    """
    Serializer for Wallet
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'balance', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'balance', 'created_at', 'updated_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Wallet Transactions
    """
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'wallet', 'transaction_type', 'amount',
            'balance_after', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'balance_after', 'created_at']


class RefundSerializer(serializers.ModelSerializer):
    """
    Serializer for Refunds
    """
    payment = PaymentSerializer(read_only=True)
    processed_by_name = serializers.CharField(
        source='processed_by.username',
        read_only=True
    )
    
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'amount', 'reason', 'status',
            'processed_by', 'processed_by_name', 'admin_notes',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'status', 'processed_by', 'created_at',
            'updated_at', 'completed_at'
        ]