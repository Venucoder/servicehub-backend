from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Service, ServiceCategory, ServiceReview, ServicePackage, ServiceFAQ

User = get_user_model()


class ServiceCategorySerializer(serializers.ModelSerializer):
    """
    Service category serializer
    """
    services_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'services_count']
    
    def get_services_count(self, obj):
        return obj.services.filter(status='active').count()


class ServiceProviderSerializer(serializers.ModelSerializer):
    """
    Service provider basic info serializer
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture']


class ServicePackageSerializer(serializers.ModelSerializer):
    """
    Service package serializer
    """
    delivery_time_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = ServicePackage
        fields = [
            'id', 'package_type', 'name', 'description', 'price',
            'delivery_time', 'delivery_time_unit', 'delivery_time_display',
            'features', 'revisions', 'is_active'
        ]


class ServiceSerializer(serializers.ModelSerializer):
    """
    Service list serializer
    """
    provider = ServiceProviderSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    delivery_time_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'slug', 'short_description', 'base_price',
            'currency', 'delivery_time_display', 'featured_image',
            'rating', 'reviews_count', 'orders_count', 'views_count',
            'provider', 'category', 'created_at'
        ]


class ServiceFAQSerializer(serializers.ModelSerializer):
    """
    Service FAQ serializer
    """
    class Meta:
        model = ServiceFAQ
        fields = ['id', 'question', 'answer', 'order']


class ServiceReviewSerializer(serializers.ModelSerializer):
    """
    Service review serializer
    """
    customer = ServiceProviderSerializer(read_only=True)
    
    class Meta:
        model = ServiceReview
        fields = [
            'id', 'customer', 'rating', 'title', 'comment',
            'communication_rating', 'service_quality_rating', 'delivery_time_rating',
            'is_featured', 'provider_response', 'provider_response_date',
            'created_at'
        ]
        read_only_fields = ['customer', 'provider_response', 'provider_response_date']


class ServiceDetailSerializer(serializers.ModelSerializer):
    """
    Detailed service serializer
    """
    provider = ServiceProviderSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    packages = ServicePackageSerializer(many=True, read_only=True)
    faqs = ServiceFAQSerializer(many=True, read_only=True)
    reviews = ServiceReviewSerializer(many=True, read_only=True)
    delivery_time_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'base_price', 'currency', 'delivery_time', 'delivery_time_unit',
            'delivery_time_display', 'requirements', 'what_you_get',
            'featured_image', 'gallery_images', 'video_url',
            'status', 'views_count', 'orders_count', 'rating', 'reviews_count',
            'meta_title', 'meta_description', 'provider', 'category',
            'packages', 'faqs', 'reviews', 'created_at', 'updated_at'
        ]


class ServiceCreateSerializer(serializers.ModelSerializer):
    """
    Service creation serializer
    """
    packages = ServicePackageSerializer(many=True, required=False)
    faqs = ServiceFAQSerializer(many=True, required=False)
    
    class Meta:
        model = Service
        fields = [
            'title', 'description', 'short_description', 'category',
            'base_price', 'currency', 'delivery_time', 'delivery_time_unit',
            'requirements', 'what_you_get', 'featured_image', 'gallery_images',
            'video_url', 'meta_title', 'meta_description', 'packages', 'faqs'
        ]
    
    def create(self, validated_data):
        packages_data = validated_data.pop('packages', [])
        faqs_data = validated_data.pop('faqs', [])
        
        service = Service.objects.create(**validated_data)
        
        # Create packages
        for package_data in packages_data:
            ServicePackage.objects.create(service=service, **package_data)
        
        # Create FAQs
        for faq_data in faqs_data:
            ServiceFAQ.objects.create(service=service, **faq_data)
        
        return service
    
    def update(self, instance, validated_data):
        packages_data = validated_data.pop('packages', [])
        faqs_data = validated_data.pop('faqs', [])
        
        # Update service
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update packages (simple approach - delete and recreate)
        if packages_data:
            instance.packages.all().delete()
            for package_data in packages_data:
                ServicePackage.objects.create(service=instance, **package_data)
        
        # Update FAQs (simple approach - delete and recreate)
        if faqs_data:
            instance.faqs.all().delete()
            for faq_data in faqs_data:
                ServiceFAQ.objects.create(service=instance, **faq_data)
        
        return instance


class ServiceUpdateSerializer(serializers.ModelSerializer):
    """
    Service update serializer (for providers to update their services)
    """
    class Meta:
        model = Service
        fields = [
            'title', 'description', 'short_description', 'base_price',
            'delivery_time', 'delivery_time_unit', 'requirements',
            'what_you_get', 'featured_image', 'gallery_images', 'video_url',
            'status', 'meta_title', 'meta_description'
        ]
    
    def validate_status(self, value):
        # Only allow certain status transitions
        if self.instance and self.instance.status == 'inactive' and value == 'active':
            # Could add additional validation here
            pass
        return value