# backend/apps/services/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from decimal import Decimal
from .models import (
    ServiceCategory,
    ServiceProvider,
    Service,
    PrepaidCardOption,
    PrepaidCard,
    CardUsage
)
from .serializers import (
    ServiceCategorySerializer,
    ServiceProviderSerializer,
    ServiceSerializer,
    ServiceListSerializer,
    PrepaidCardOptionSerializer,
    PrepaidCardOptionCreateSerializer,
    PrepaidCardSerializer,
    PrepaidCardListSerializer,
    CreatePrepaidCardSerializer,
    UseCardSerializer,
    CardUsageSerializer
)


# ============================================
# Category & Provider ViewSets
# ============================================

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


# ============================================
# Service ViewSet
# ============================================

class ServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for Services"""
    queryset = Service.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_available', 'supports_prepaid_cards']
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
    def prepaid_card_options(self, request, pk=None):
        """Get prepaid card options for a service"""
        service = self.get_object()
        
        if not service.supports_prepaid_cards:
            return Response({
                'message': 'This service does not support prepaid cards',
                'options': []
            })
        
        options = PrepaidCardOption.objects.filter(
            service=service,
            is_active=True
        ).order_by('display_order', 'total_units')
        
        serializer = PrepaidCardOptionSerializer(options, many=True)
        return Response(serializer.data)


# ============================================
# Prepaid Card Option ViewSet
# ============================================

class PrepaidCardOptionViewSet(viewsets.ModelViewSet):
    """ViewSet for Prepaid Card Options (Providers create, Customers view)"""
    queryset = PrepaidCardOption.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['service', 'is_active']
    ordering_fields = ['display_order', 'price', 'total_units']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PrepaidCardOptionCreateSerializer
        return PrepaidCardOptionSerializer
    
    def get_queryset(self):
        """Providers see their options, customers see active options"""
        user = self.request.user
        if user.role == 'provider':
            return PrepaidCardOption.objects.filter(service__provider__user=user)
        return PrepaidCardOption.objects.filter(is_active=True)
    
    def perform_create(self, serializer):
        """Only providers can create card options for their services"""
        service = serializer.validated_data['service']
        if service.provider.user != self.request.user:
            raise permissions.PermissionDenied("You can only create options for your own services")
        serializer.save()


# ============================================
# Prepaid Card ViewSet
# ============================================

class PrepaidCardViewSet(viewsets.ModelViewSet):
    """ViewSet for Prepaid Cards (Customer's purchased cards)"""
    queryset = PrepaidCard.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['purchased_at', 'last_used_at']
    http_method_names = ['get', 'post', 'delete']  # No PUT/PATCH
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return CreatePrepaidCardSerializer
        elif self.action == 'list':
            return PrepaidCardListSerializer
        return PrepaidCardSerializer
    
    def get_queryset(self):
        """Users see only their own prepaid cards"""
        user = self.request.user
        if user.role == 'admin':
            return PrepaidCard.objects.all()
        return PrepaidCard.objects.filter(customer=user)
    
    def perform_create(self, serializer):
        """Buy/Create prepaid card"""
        card_option_id = serializer.validated_data.get('card_option_id')
        card_option = PrepaidCardOption.objects.get(id=card_option_id)
        
        # Create the prepaid card
        serializer.save(
            customer=self.request.user,
            card_option=card_option,
            total_units=card_option.total_units,
            total_amount=card_option.price,
            per_unit_price=card_option.price_per_unit
        )
    
    @action(detail=True, methods=['post'])
    def use_units(self, request, pk=None):
        """
        Mark units as used (digital punch card)
        POST /api/services/prepaid-cards/{id}/use_units/
        Body: {"units": 1.5, "notes": "Picked up at shop"}
        """
        card = self.get_object()
        serializer = UseCardSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        units = serializer.validated_data['units']
        notes = serializer.validated_data.get('notes', '')
        
        # Use the units
        success, message = card.use_units(units)
        
        if not success:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create usage record
        CardUsage.objects.create(
            card=card,
            units_used=units,
            marked_by=request.user,
            notes=notes
        )
        
        return Response({
            'message': message,
            'used_units': str(card.used_units),
            'remaining_units': str(card.remaining_units),
            'status': card.status
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel prepaid card"""
        card = self.get_object()
        
        if card.cancel():
            return Response({
                'message': 'Prepaid card cancelled successfully',
                'status': card.status
            })
        
        return Response(
            {'error': 'Cannot cancel this card'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'])
    def usage_history(self, request, pk=None):
        """Get usage history for prepaid card"""
        card = self.get_object()
        usage = CardUsage.objects.filter(card=card).order_by('-used_at')
        serializer = CardUsageSerializer(usage, many=True)
        return Response(serializer.data)


# ============================================
# Card Usage ViewSet
# ============================================

class CardUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Card Usage (Read-only, history tracking)"""
    queryset = CardUsage.objects.all()
    serializer_class = CardUsageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['card']
    ordering_fields = ['used_at']
    
    def get_queryset(self):
        """Users see their own usage history"""
        user = self.request.user
        if user.role == 'admin':
            return CardUsage.objects.all()
        return CardUsage.objects.filter(card__customer=user)