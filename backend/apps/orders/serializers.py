# backend/apps/orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderStatusHistory
from apps.services.serializers import ServiceListSerializer
from apps.users.serializers import UserSerializer


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for Order Status History"""
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


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for order listings"""
    service_name = serializers.CharField(source='service.name', read_only=True)
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'service_name', 
            'status', 'delivery_type', 'quantity', 'quantity_label',
            'total_amount', 'scheduled_date', 'created_at'
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Full serializer for Orders"""
    customer = UserSerializer(read_only=True)
    service = ServiceListSerializer(read_only=True)
    service_id = serializers.UUIDField(write_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'service', 'service_id',
            'status', 'quantity', 'quantity_label',
            'unit_price', 'total_amount', 'delivery_type',
            'delivery_address', 'scheduled_date', 'scheduled_time',
            'expected_delivery_time', 'notes', 'status_history',
            'created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'customer',
            'expected_delivery_time', 'created_at', 'updated_at',
            'confirmed_at', 'completed_at', 'cancelled_at'
        ]


class CreateOrderSerializer(serializers.ModelSerializer):
    """Serializer for creating one-time orders"""
    
    class Meta:
        model = Order
        fields = [
            'service_id', 'quantity', 'quantity_label',
            'delivery_type', 'delivery_address',
            'scheduled_date', 'scheduled_time', 'notes'
        ]
    
    service_id = serializers.UUIDField()
    
    def validate(self, attrs):
        """Validate order creation"""
        # Validate quantity
        quantity = attrs.get('quantity', 0)
        if quantity <= 0:
            raise serializers.ValidationError({
                'quantity': 'Quantity must be greater than 0'
            })
        
        # Validate delivery type
        delivery_type = attrs.get('delivery_type')
        
        # If scheduled, require date and time
        if delivery_type == 'scheduled':
            if not attrs.get('scheduled_date'):
                raise serializers.ValidationError({
                    'scheduled_date': 'Scheduled date is required for scheduled delivery'
                })
            if not attrs.get('scheduled_time'):
                raise serializers.ValidationError({
                    'scheduled_time': 'Scheduled time is required for scheduled delivery'
                })
        
        # Validate delivery address
        if not attrs.get('delivery_address') or not attrs.get('delivery_address').strip():
            raise serializers.ValidationError({
                'delivery_address': 'Delivery address is required'
            })
        
        return attrs


class UpdateOrderStatusSerializer(serializers.Serializer):
    """Serializer for updating order status"""
    status = serializers.ChoiceField(
        choices=[choice[0] for choice in Order.ORDER_STATUS]
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )