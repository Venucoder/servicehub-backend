# backend/apps/orders/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from decimal import Decimal
from .models import Order, OrderStatusHistory
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    CreateOrderSerializer,
    OrderStatusHistorySerializer,
    UpdateOrderStatusSerializer
)
from apps.services.models import Service


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for One-time Orders
    """
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'delivery_type']
    ordering_fields = ['created_at', 'scheduled_date']
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return CreateOrderSerializer
        elif self.action == 'list':
            return OrderListSerializer
        return OrderSerializer
    
    def get_queryset(self):
        """
        Customers see their orders, providers see orders for their services
        """
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.all()
        elif user.role == 'provider':
            return Order.objects.filter(service__provider__user=user)
        return Order.objects.filter(customer=user)
    
    def perform_create(self, serializer):
        """
        Create one-time order with automatic calculations
        """
        service_id = serializer.validated_data.get('service_id')
        quantity = serializer.validated_data.get('quantity')
        quantity_label = serializer.validated_data.get('quantity_label', '')
        
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            raise serializers.ValidationError({'service_id': 'Service not found'})
        
        # Check if service is available
        if not service.is_available:
            raise serializers.ValidationError({'service_id': 'Service is not available'})
        
        # Calculate prices
        # If quantity_label is provided, try to find matching price from quantity_options
        unit_price = service.base_price
        
        if quantity_label and service.quantity_options:
            # Try to find price from quantity_options
            for option in service.quantity_options:
                if option.get('label') == quantity_label:
                    unit_price = Decimal(str(option.get('price', service.base_price)))
                    break
        
        total_amount = unit_price * quantity
        
        # Create order
        serializer.save(
            customer=self.request.user,
            service=service,
            unit_price=unit_price,
            total_amount=total_amount
        )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update order status
        POST /api/orders/{id}/update_status/
        Body: {"status": "confirmed", "notes": "Order confirmed"}
        """
        order = self.get_object()
        serializer = UpdateOrderStatusSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            from_status=order.status,
            to_status=new_status,
            changed_by=request.user,
            notes=notes
        )
        
        # Update order status
        old_status = order.status
        order.status = new_status
        
        # Update timestamps based on status
        if new_status == 'confirmed' and old_status == 'pending':
            from django.utils import timezone
            order.confirmed_at = timezone.now()
        elif new_status == 'completed':
            from django.utils import timezone
            order.completed_at = timezone.now()
        elif new_status == 'cancelled':
            from django.utils import timezone
            order.cancelled_at = timezone.now()
        
        order.save()
        
        return Response({
            'message': 'Order status updated successfully',
            'status': order.status,
            'order_number': order.order_number
        })
    
    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        """
        Get order status history
        GET /api/orders/{id}/status_history/
        """
        order = self.get_object()
        history = OrderStatusHistory.objects.filter(order=order)
        serializer = OrderStatusHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel order (customer or provider can cancel pending/confirmed orders)
        POST /api/orders/{id}/cancel/
        """
        order = self.get_object()
        
        # Check permissions
        if order.customer != request.user and request.user.role != 'provider' and request.user.role != 'admin':
            return Response(
                {'error': 'You do not have permission to cancel this order'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if order.cancel():
            # Create history record
            OrderStatusHistory.objects.create(
                order=order,
                from_status='pending' if order.status == 'cancelled' else order.status,
                to_status='cancelled',
                changed_by=request.user,
                notes=request.data.get('reason', 'Order cancelled by user')
            )
            
            return Response({
                'message': 'Order cancelled successfully',
                'order_number': order.order_number
            })
        
        return Response(
            {'error': 'Cannot cancel this order. Only pending or confirmed orders can be cancelled.'},
            status=status.HTTP_400_BAD_REQUEST
        )