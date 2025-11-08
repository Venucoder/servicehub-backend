from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Order, OrderStatusHistory
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    CreateOrderSerializer,
    OrderStatusHistorySerializer
)
from apps.services.models import Service


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Orders
    """
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'order_type']
    ordering_fields = ['created_at', 'delivery_date']
    
    def get_serializer_class(self):
        """
        Use different serializers for different actions
        """
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
        Create order with automatic calculations
        """
        service_id = self.request.data.get('service_id')
        service = Service.objects.get(id=service_id)
        quantity = serializer.validated_data.get('quantity', 1)
        
        # Calculate prices
        unit_price = service.base_price
        total_amount = unit_price * quantity
        
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
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            from_status=order.status,
            to_status=new_status,
            changed_by=request.user,
            notes=notes
        )
        
        # Update order status
        order.status = new_status
        order.save()
        
        return Response({
            'message': 'Order status updated successfully',
            'status': order.status
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