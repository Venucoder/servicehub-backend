from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import (
    ServiceCategory,
    ServiceProvider,
    Service,
    SubscriptionPackage,
    Subscription,
    SubscriptionUsage
)
from .serializers import (
    ServiceCategorySerializer,
    ServiceProviderSerializer,
    ServiceSerializer,
    ServiceListSerializer,
    SubscriptionPackageSerializer,
    SubscriptionSerializer,
    SubscriptionListSerializer,
    CreateSubscriptionSerializer,
    SubscriptionUsageSerializer
)


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Service Categories (Read-only for customers)"""
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.AllowAny]


class ServiceProviderViewSet(viewsets.ModelViewSet):
    """ViewSet for Service Providers"""
    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['business_name', 'business_email']
    ordering_fields = ['average_rating', 'created_at']
    
    def get_queryset(self):
        """Providers see their own, admins see all"""
        user = self.request.user
        if user.role == 'admin':
            return ServiceProvider.objects.all()
        elif user.role == 'provider':
            return ServiceProvider.objects.filter(user=user)
        return ServiceProvider.objects.filter(status='active')
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current provider's profile"""
        if request.user.role != 'provider':
            return Response(
                {'error': 'Only service providers can access this'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            provider = ServiceProvider.objects.get(user=request.user)
            serializer = self.get_serializer(provider)
            return Response(serializer.data)
        except ServiceProvider.DoesNotExist:
            return Response(
                {'error': 'Service provider profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for Services"""
    queryset = Service.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'pricing_type', 'is_available']
    search_fields = ['name', 'description']
    ordering_fields = ['base_price', 'created_at']
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'list':
            return ServiceListSerializer
        return ServiceSerializer
    
    def get_queryset(self):
        """Providers see their own services, customers see available services"""
        user = self.request.user
        if user.is_authenticated and user.role == 'provider':
            return Service.objects.filter(provider__user=user)
        return Service.objects.filter(is_active=True, is_available=True)
    
    def perform_create(self, serializer):
        """Automatically set provider when creating service"""
        provider = ServiceProvider.objects.get(user=self.request.user)
        serializer.save(provider=provider)
    
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """Update service stock"""
        service = self.get_object()
        
        if service.provider.user != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'You can only update your own services'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stock = request.data.get('stock')
        if stock is None:
            return Response(
                {'error': 'Stock value is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service.current_stock = stock
        service.save()
        
        return Response({
            'message': 'Stock updated successfully',
            'current_stock': service.current_stock
        })
    
    @action(detail=True, methods=['get'])
    def packages(self, request, pk=None):
        """Get subscription packages for a service"""
        service = self.get_object()
        packages = SubscriptionPackage.objects.filter(
            service=service,
            is_active=True
        )
        serializer = SubscriptionPackageSerializer(packages, many=True)
        return Response(serializer.data)


class SubscriptionPackageViewSet(viewsets.ModelViewSet):
    """ViewSet for Subscription Packages"""
    queryset = SubscriptionPackage.objects.all()
    serializer_class = SubscriptionPackageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['service', 'is_active']
    ordering_fields = ['display_order', 'price', 'units']
    
    def get_queryset(self):
        """Providers see their packages, customers see active packages"""
        user = self.request.user
        if user.role == 'provider':
            return SubscriptionPackage.objects.filter(service__provider__user=user)
        return SubscriptionPackage.objects.filter(is_active=True)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for Subscriptions"""
    queryset = Subscription.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'delivery_type']
    ordering_fields = ['created_at']
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return CreateSubscriptionSerializer
        elif self.action == 'list':
            return SubscriptionListSerializer
        return SubscriptionSerializer
    
    def get_queryset(self):
        """Users see only their own subscriptions"""
        user = self.request.user
        if user.role == 'admin':
            return Subscription.objects.all()
        return Subscription.objects.filter(customer=user)
    
    def perform_create(self, serializer):
        """Create subscription with automatic calculations"""
        package_id = self.request.data.get('package_id')
        package = SubscriptionPackage.objects.get(id=package_id)
        
        serializer.save(
            customer=self.request.user,
            package=package,
            total_units=package.units,
            total_amount=package.price,
            per_unit_price=package.price_per_unit
        )
    
    @action(detail=True, methods=['post'])
    def use_units(self, request, pk=None):
        """
        Mark units as used (digital punch card)
        POST /api/subscriptions/{id}/use_units/
        Body: {"units": 1, "usage_type": "pickup" or "delivered"}
        """
        subscription = self.get_object()
        
        units = request.data.get('units', 1)
        usage_type = request.data.get('usage_type', 'pickup')
        notes = request.data.get('notes', '')
        
        # Validate
        success, message = subscription.use_units(units)
        if not success:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create usage record
        usage_data = {
            'subscription': subscription,
            'units_used': units,
            'usage_type': usage_type,
            'notes': notes
        }
        
        if usage_type == 'pickup':
            usage_data['picked_up_at'] = timezone.now()
        else:
            usage_data['delivered_at'] = timezone.now()
            usage_data['delivered_by'] = request.user
        
        SubscriptionUsage.objects.create(**usage_data)
        
        return Response({
            'message': message,
            'used_units': subscription.used_units,
            'remaining_units': subscription.remaining_units,
            'status': subscription.status
        })
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause subscription"""
        subscription = self.get_object()
        
        if subscription.pause():
            return Response({
                'message': 'Subscription paused successfully',
                'status': subscription.status
            })
        
        return Response(
            {'error': 'Cannot pause this subscription'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume subscription"""
        subscription = self.get_object()
        
        if subscription.resume():
            return Response({
                'message': 'Subscription resumed successfully',
                'status': subscription.status
            })
        
        return Response(
            {'error': 'Cannot resume this subscription'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel subscription"""
        subscription = self.get_object()
        
        if subscription.cancel():
            return Response({
                'message': 'Subscription cancelled successfully',
                'status': subscription.status
            })
        
        return Response(
            {'error': 'Cannot cancel this subscription'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'])
    def usage_history(self, request, pk=None):
        """Get usage history for subscription"""
        subscription = self.get_object()
        usage = SubscriptionUsage.objects.filter(subscription=subscription)
        serializer = SubscriptionUsageSerializer(usage, many=True)
        return Response(serializer.data)


class SubscriptionUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Subscription Usage (Read-only)"""
    queryset = SubscriptionUsage.objects.all()
    serializer_class = SubscriptionUsageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['subscription', 'usage_type']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        """Users see their own usage history"""
        user = self.request.user
        if user.role == 'admin':
            return SubscriptionUsage.objects.all()
        return SubscriptionUsage.objects.filter(subscription__customer=user)