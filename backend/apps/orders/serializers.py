from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from apps.services.serializers import ServiceListSerializer
from apps.users.serializers import UserSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for Order Items
    """
    service = ServiceListSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'service', 'quantity', 'unit_price', 'total_price'
        ]
        read_only_fields = ['id', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Orders
    """
    customer = UserSerializer(read_only=True)
    service = ServiceListSerializer(read_only=True)
    service_id = serializers.UUIDField(write_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'service', 'service_id',
            'subscription', 'order_type', 'status', 'quantity',
            'unit_price', 'total_amount', 'delivery_address',
            'delivery_date', 'delivery_time_slot', 'notes',
            'items', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'customer', 'created_at',
            'updated_at', 'completed_at'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for order listings
    """
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'service_name', 'status',
            'total_amount', 'delivery_date', 'created_at'
        ]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for Order Status History
    """
    changed_by_name = serializers.CharField(
        source='changed_by.username',
        read_only=True
    )
    
    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'order', 'from_status', 'to_status',
            'changed_by', 'changed_by_name', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CreateOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for creating orders
    """
    class Meta:
        model = Order
        fields = [
            'service_id', 'order_type', 'quantity', 'delivery_address',
            'delivery_date', 'delivery_time_slot', 'notes'
        ]
    
    service_id = serializers.UUIDField()
    
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value