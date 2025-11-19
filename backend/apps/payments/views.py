# backend/apps/payments/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Payment, Wallet, WalletTransaction, Refund
from .serializers import (
    PaymentSerializer,
    PaymentListSerializer,
    CreatePaymentSerializer,
    WalletSerializer,
    WalletTransactionSerializer,
    RefundSerializer,
    CreateRefundSerializer
)
from apps.orders.models import Order
from apps.services.models import PrepaidCard


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Payments
    """
    queryset = Payment.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_method']
    
    def get_queryset(self):
        """Users see only their payments"""
        user = self.request.user
        if user.role == 'admin':
            return Payment.objects.all()
        return Payment.objects.filter(customer=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePaymentSerializer
        elif self.action == 'list':
            return PaymentListSerializer
        return PaymentSerializer
    
    def perform_create(self, serializer):
        """
        Create payment for an order or prepaid card
        """
        order_id = serializer.validated_data.get('order_id')
        prepaid_card_id = serializer.validated_data.get('prepaid_card_id')
        
        payment_data = {
            'customer': self.request.user,
            'payment_method': serializer.validated_data['payment_method'],
            'notes': serializer.validated_data.get('notes', ''),
            'status': 'pending'
        }
        
        # Payment for Order
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                if order.customer != self.request.user:
                    raise permissions.PermissionDenied("This is not your order")
                
                payment_data['order'] = order
                payment_data['amount'] = order.total_amount
                
            except Order.DoesNotExist:
                raise serializers.ValidationError({'order_id': 'Order not found'})
        
        # Payment for Prepaid Card
        elif prepaid_card_id:
            try:
                card = PrepaidCard.objects.get(id=prepaid_card_id)
                if card.customer != self.request.user:
                    raise permissions.PermissionDenied("This is not your prepaid card")
                
                payment_data['prepaid_card'] = card
                payment_data['amount'] = card.total_amount
                
            except PrepaidCard.DoesNotExist:
                raise serializers.ValidationError({'prepaid_card_id': 'Prepaid card not found'})
        
        # Create payment
        Payment.objects.create(**payment_data)


class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Wallet (Read-only, balance updated via transactions)
    """
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users see only their wallet"""
        return Wallet.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """
        Get current user's wallet
        GET /api/payments/wallets/my_wallet/
        """
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """
        Get wallet transaction history
        GET /api/payments/wallets/transactions/
        """
        wallet = Wallet.objects.get(user=request.user)
        transactions = WalletTransaction.objects.filter(wallet=wallet)
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class RefundViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Refunds
    """
    queryset = Refund.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    
    def get_queryset(self):
        """Users see their refunds, admins see all"""
        user = self.request.user
        if user.role == 'admin':
            return Refund.objects.all()
        return Refund.objects.filter(payment__customer=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateRefundSerializer
        return RefundSerializer
    
    def perform_create(self, serializer):
        """Create refund request"""
        payment_id = serializer.validated_data['payment_id']
        payment = Payment.objects.get(id=payment_id)
        
        # Check ownership
        if payment.customer != self.request.user:
            raise permissions.PermissionDenied("This is not your payment")
        
        serializer.save(payment=payment)