from rest_framework import serializers
from .models import (
    ServiceCategory,
    ServiceProvider,
    Service,
    SubscriptionPackage,
    Subscription,
    SubscriptionUsage
)
from apps.users.serializers import UserSerializer


class ServiceCategorySerializer(serializers.ModelSerializer):
    """Serializer for Service Categories"""
    
    class Meta:
        model = ServiceCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ServiceProviderSerializer(serializers.ModelSerializer):
    """Serializer for Service Providers"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ServiceProvider
        fields = [
            'id', 'user', 'business_name', 'business_address',
            'business_phone', 'business_email', 'status',
            'gst_number', 'pan_number', 'average_rating',
            'total_ratings', 'verified_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'average_rating', 'total_ratings',
            'verified_at', 'created_at'
        ]


class ServiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for service listings"""
    provider_name = serializers.CharField(source='provider.business_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'provider_name', 'category_name',
            'base_price', 'unit', 'is_available', 'current_stock',
            'supports_immediate_delivery'
        ]


class ServiceSerializer(serializers.ModelSerializer):
    """Full serializer for Services"""
    provider = ServiceProviderSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'provider', 'category', 'category_id', 'name',
            'description', 'pricing_type', 'base_price', 'unit',
            'minimum_order', 'is_active', 'is_available',
            'has_stock_tracking', 'current_stock',
            'business_hours_start', 'business_hours_end', 'operating_days',
            'supports_immediate_delivery', 'immediate_delivery_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'provider', 'created_at', 'updated_at']


class SubscriptionPackageSerializer(serializers.ModelSerializer):
    """Serializer for Subscription Packages"""
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = SubscriptionPackage
        fields = [
            'id', 'service', 'service_name', 'name', 'units',
            'price', 'price_per_unit', 'savings', 'is_active',
            'display_order', 'created_at'
        ]
        read_only_fields = ['id', 'price_per_unit', 'savings', 'created_at']


class SubscriptionUsageSerializer(serializers.ModelSerializer):
    """Serializer for Subscription Usage History"""
    
    class Meta:
        model = SubscriptionUsage
        fields = [
            'id', 'subscription', 'units_used', 'usage_type',
            'picked_up_at', 'delivered_at', 'delivered_by',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SubscriptionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for subscription listings"""
    service_name = serializers.CharField(source='package.service.name', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'service_name', 'package_name', 'status',
            'delivery_type', 'total_units', 'used_units',
            'remaining_units', 'created_at'
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    """Full serializer for Subscriptions"""
    customer = UserSerializer(read_only=True)
    package = SubscriptionPackageSerializer(read_only=True)
    package_id = serializers.UUIDField(write_only=True)
    usage_history = SubscriptionUsageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'customer', 'package', 'package_id', 'status',
            'delivery_type', 'total_units', 'used_units', 'remaining_units',
            'total_amount', 'per_unit_price',
            'delivery_address', 'preferred_time', 'delivery_days',
            'units_per_delivery', 'usage_history',
            'created_at', 'updated_at', 'paused_at', 'completed_at', 'cancelled_at'
        ]
        read_only_fields = [
            'id', 'customer', 'remaining_units', 'created_at', 'updated_at',
            'paused_at', 'completed_at', 'cancelled_at'
        ]


class CreateSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for creating subscriptions"""
    
    class Meta:
        model = Subscription
        fields = [
            'package_id', 'delivery_type', 'delivery_address',
            'preferred_time', 'delivery_days', 'units_per_delivery'
        ]
    
    package_id = serializers.UUIDField()
    
    def validate(self, attrs):
        """Validate subscription creation"""
        if attrs.get('delivery_type') == 'auto_delivery':
            if not attrs.get('delivery_address'):
                raise serializers.ValidationError({
                    'delivery_address': 'Delivery address is required for auto-delivery'
                })
            if not attrs.get('preferred_time'):
                raise serializers.ValidationError({
                    'preferred_time': 'Preferred time is required for auto-delivery'
                })
        return attrs