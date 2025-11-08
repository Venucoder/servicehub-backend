from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Payment, Wallet, WalletTransaction, Refund
from .serializers import (
    PaymentSerializer,
    CreatePaymentSerializer,
    WalletSerializer,
    WalletTransactionSerializer,
    RefundSerializer
)
from apps.orders.models import Order


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Payments
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_method']
    
    def get_queryset(self):
        """
        Users see only their payments
        """
        user = self.request.user
        if user.role == 'admin':
            return Payment.objects.all()
        return Payment.objects.filter(customer=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePaymentSerializer
        return PaymentSerializer
    
    def perform_create(self, serializer):
        """
        Create payment for an order
        """
        order_id = self.request.data.get('order')
        order = Order.objects.get(id=order_id)
        
        serializer.save(
            customer=self.request.user,
            amount=order.total_amount
        )


class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Wallet (Read-only, balance updated via transactions)
    """
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Users see only their wallet
        """
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
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    
    def get_queryset(self):
        """
        Users see their refunds, admins see all
        """
        user = self.request.user
        if user.role == 'admin':
            return Refund.objects.all()
        return Refund.objects.filter(payment__customer=user)