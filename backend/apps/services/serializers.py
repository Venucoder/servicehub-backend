from rest_framework import serializers
from .models import ServiceCategory, ServiceProvider, Service, Subscription
from apps.users.serializers import UserSerializer


class ServiceCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Service Categories
    """
    class Meta:
        model = ServiceCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ServiceProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for Service Providers
    """
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


class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializer for Services
    """
    provider = ServiceProviderSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'provider', 'category', 'category_id', 'name',
            'description', 'pricing_type', 'base_price',
            'subscription_price', 'unit', 'minimum_order',
            'is_active', 'is_available', 'has_stock_tracking',
            'current_stock', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'provider', 'created_at', 'updated_at']


class ServiceListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for service listings
    """
    provider_name = serializers.CharField(source='provider.business_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'provider_name', 'category_name',
            'base_price', 'subscription_price', 'unit',
            'is_available', 'current_stock'
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for Subscriptions
    """
    customer = UserSerializer(read_only=True)
    service = ServiceListSerializer(read_only=True)
    service_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'customer', 'service', 'service_id', 'status',
            'start_date', 'end_date', 'total_units', 'used_units',
            'remaining_units', 'total_amount', 'per_unit_price',
            'auto_renew', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'customer', 'remaining_units', 'created_at', 'updated_at'
        ]