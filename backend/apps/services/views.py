from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import ServiceCategory, ServiceProvider, Service, Subscription
from .serializers import (
    ServiceCategorySerializer,
    ServiceProviderSerializer,
    ServiceSerializer,
    ServiceListSerializer,
    SubscriptionSerializer
)


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Service Categories (Read-only for customers)
    """
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.AllowAny]


class ServiceProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Service Providers
    """
    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['business_name', 'business_email']
    ordering_fields = ['average_rating', 'created_at']
    
    def get_queryset(self):
        """
        Providers see their own, admins see all
        """
        user = self.request.user
        if user.role == 'admin':
            return ServiceProvider.objects.all()
        elif user.role == 'provider':
            return ServiceProvider.objects.filter(user=user)
        return ServiceProvider.objects.filter(status='active')
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """
        Get current provider's profile
        GET /api/services/providers/my_profile/
        """
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
    """
    ViewSet for Services
    """
    queryset = Service.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'pricing_type', 'is_available']
    search_fields = ['name', 'description']
    ordering_fields = ['base_price', 'created_at']
    
    def get_serializer_class(self):
        """
        Use different serializers for list and detail views
        """
        if self.action == 'list':
            return ServiceListSerializer
        return ServiceSerializer
    
    def get_queryset(self):
        """
        Providers see their own services, customers see available services
        """
        user = self.request.user
        if user.is_authenticated and user.role == 'provider':
            return Service.objects.filter(provider__user=user)
        return Service.objects.filter(is_active=True, is_available=True)
    
    def perform_create(self, serializer):
        """
        Automatically set provider when creating service
        """
        provider = ServiceProvider.objects.get(user=self.request.user)
        serializer.save(provider=provider)
    
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """
        Update service stock
        POST /api/services/{id}/update_stock/
        Body: {"stock": 50}
        """
        service = self.get_object()
        
        # Only provider can update their own stock
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


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Subscriptions
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'auto_renew']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    
    def get_queryset(self):
        """
        Users see only their own subscriptions
        """
        user = self.request.user
        if user.role == 'admin':
            return Subscription.objects.all()
        return Subscription.objects.filter(customer=user)
    
    def perform_create(self, serializer):
        """
        Automatically set customer when creating subscription
        """
        serializer.save(customer=self.request.user)
    
    @action(detail=True, methods=['post'])
    def use_unit(self, request, pk=None):
        """
        Mark one unit as used (like marking a box on the card)
        POST /api/subscriptions/{id}/use_unit/
        """
        subscription = self.get_object()
        
        if subscription.status != 'active':
            return Response(
                {'error': 'Subscription is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if subscription.remaining_units <= 0:
            return Response(
                {'error': 'No units remaining'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription.used_units += 1
        subscription.save()
        
        return Response({
            'message': 'Unit marked as used',
            'used_units': subscription.used_units,
            'remaining_units': subscription.remaining_units
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel subscription
        POST /api/subscriptions/{id}/cancel/
        """
        subscription = self.get_object()
        subscription.status = 'cancelled'
        subscription.save()
        
        return Response({
            'message': 'Subscription cancelled successfully'
        })