# backend/apps/services/serializers.py
from rest_framework import serializers
from .models import (
    ServiceCategory,
    ServiceProvider,
    Service,
    PrepaidCardOption,
    PrepaidCard,
    CardUsage
)
from apps.users.serializers import UserSerializer


# ============================================
# Category & Provider Serializers
# ============================================

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


# ============================================
# Service Serializers
# ============================================

class ServiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for service listings"""
    provider_name = serializers.CharField(source='provider.business_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'provider_name', 'category_name',
            'base_price', 'unit', 'is_available', 'current_stock',
            'supports_immediate_delivery', 'supports_prepaid_cards'
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
            'description', 'base_price', 'unit', 'quantity_options',
            'minimum_order', 'is_active', 'is_available',
            'has_stock_tracking', 'current_stock',
            'business_hours_start', 'business_hours_end', 'operating_days',
            'supports_immediate_delivery', 'immediate_delivery_time',
            'supports_prepaid_cards',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'provider', 'created_at', 'updated_at']


# ============================================
# Prepaid Card Option Serializers
# ============================================

class PrepaidCardOptionSerializer(serializers.ModelSerializer):
    """Serializer for Prepaid Card Options"""
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = PrepaidCardOption
        fields = [
            'id', 'service', 'service_name', 'name', 'total_units',
            'price', 'price_per_unit', 'savings', 'is_active',
            'display_order', 'created_at'
        ]
        read_only_fields = ['id', 'price_per_unit', 'savings', 'created_at']


class PrepaidCardOptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Prepaid Card Options"""
    
    class Meta:
        model = PrepaidCardOption
        fields = [
            'service', 'name', 'total_units', 'price', 'display_order'
        ]
    
    def validate(self, attrs):
        """Validate prepaid card option"""
        if attrs.get('total_units', 0) <= 0:
            raise serializers.ValidationError({
                'total_units': 'Total units must be greater than 0'
            })
        if attrs.get('price', 0) <= 0:
            raise serializers.ValidationError({
                'price': 'Price must be greater than 0'
            })
        return attrs


# ============================================
# Prepaid Card Serializers
# ============================================

class CardUsageSerializer(serializers.ModelSerializer):
    """Serializer for Card Usage History"""
    marked_by_name = serializers.CharField(source='marked_by.username', read_only=True)
    
    class Meta:
        model = CardUsage
        fields = [
            'id', 'card', 'units_used', 'marked_by', 'marked_by_name',
            'notes', 'used_at'
        ]
        read_only_fields = ['id', 'used_at']


class PrepaidCardListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for prepaid card listings"""
    service_name = serializers.CharField(source='card_option.service.name', read_only=True)
    card_name = serializers.CharField(source='card_option.name', read_only=True)
    
    class Meta:
        model = PrepaidCard
        fields = [
            'id', 'service_name', 'card_name', 'status',
            'total_units', 'used_units', 'remaining_units',
            'purchased_at', 'last_used_at'
        ]


class PrepaidCardSerializer(serializers.ModelSerializer):
    """Full serializer for Prepaid Cards"""
    customer = UserSerializer(read_only=True)
    card_option = PrepaidCardOptionSerializer(read_only=True)
    card_option_id = serializers.UUIDField(write_only=True)
    usage_history = CardUsageSerializer(many=True, read_only=True)
    
    class Meta:
        model = PrepaidCard
        fields = [
            'id', 'customer', 'card_option', 'card_option_id', 'status',
            'total_units', 'used_units', 'remaining_units',
            'total_amount', 'per_unit_price', 'usage_history',
            'purchased_at', 'last_used_at', 'exhausted_at', 'cancelled_at'
        ]
        read_only_fields = [
            'id', 'customer', 'remaining_units', 'purchased_at',
            'last_used_at', 'exhausted_at', 'cancelled_at'
        ]


class CreatePrepaidCardSerializer(serializers.ModelSerializer):
    """Serializer for creating/buying prepaid cards"""
    
    class Meta:
        model = PrepaidCard
        fields = ['card_option_id']
    
    card_option_id = serializers.UUIDField()
    
    def validate_card_option_id(self, value):
        """Validate card option exists and is active"""
        try:
            card_option = PrepaidCardOption.objects.get(id=value)
            if not card_option.is_active:
                raise serializers.ValidationError("This card option is not available")
            if not card_option.service.is_available:
                raise serializers.ValidationError("This service is not available")
            return value
        except PrepaidCardOption.DoesNotExist:
            raise serializers.ValidationError("Card option not found")


class UseCardSerializer(serializers.Serializer):
    """Serializer for using prepaid card units"""
    units = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        help_text="Number of units to use (e.g., 1, 0.5, 2.5)"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Optional notes about usage"
    )