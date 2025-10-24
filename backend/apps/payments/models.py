from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
import uuid

User = get_user_model()


class PaymentMethod(models.Model):
    """
    Stored payment methods for users
    """
    PAYMENT_TYPES = (
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('crypto', 'Cryptocurrency'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    provider = models.CharField(max_length=50, help_text="e.g., Stripe, PayPal")
    provider_payment_method_id = models.CharField(max_length=200)
    
    # Card details (if applicable)
    last_four = models.CharField(max_length=4, blank=True)
    brand = models.CharField(max_length=20, blank=True)
    exp_month = models.PositiveIntegerField(null=True, blank=True)
    exp_year = models.PositiveIntegerField(null=True, blank=True)
    
    # General details
    nickname = models.CharField(max_length=50, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_methods'
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_default']),
        ]
    
    def __str__(self):
        if self.payment_type == 'card':
            return f"{self.brand} ending in {self.last_four}"
        return f"{self.get_payment_type_display()}"


class Transaction(models.Model):
    """
    All financial transactions in the system
    """
    TRANSACTION_TYPES = (
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('payout', 'Payout'),
        ('fee', 'Platform Fee'),
        ('bonus', 'Bonus'),
        ('penalty', 'Penalty'),
    )
    
    TRANSACTION_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(max_length=50, unique=True, blank=True)
    
    # Parties
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    
    # Payment provider details
    provider = models.CharField(max_length=50, help_text="e.g., Stripe, PayPal")
    provider_transaction_id = models.CharField(max_length=200, blank=True)
    provider_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # Platform details
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Metadata
    description = models.CharField(max_length=300)
    metadata = models.JSONField(default=dict, blank=True)
    failure_reason = models.CharField(max_length=300, blank=True)
    
    # Timestamps
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['order']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import random
            import string
            self.transaction_id = 'TXN-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        
        # Calculate net amount
        self.net_amount = self.amount - self.provider_fee - self.platform_fee
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.get_transaction_type_display()} - ${self.amount}"


class Wallet(models.Model):
    """
    User wallet for storing earnings and managing payouts
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    pending_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_withdrawn = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')
    
    # Payout settings
    minimum_payout = models.DecimalField(max_digits=10, decimal_places=2, default=50.00, validators=[MinValueValidator(0)])
    auto_payout_enabled = models.BooleanField(default=False)
    auto_payout_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=100.00, validators=[MinValueValidator(0)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wallets'
    
    def __str__(self):
        return f"{self.user.username}'s Wallet - ${self.balance}"
    
    @property
    def available_for_withdrawal(self):
        return self.balance >= self.minimum_payout


class PayoutRequest(models.Model):
    """
    Payout requests from providers
    """
    PAYOUT_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYOUT_METHODS = (
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('crypto', 'Cryptocurrency'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payout_id = models.CharField(max_length=50, unique=True, blank=True)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payout_requests')
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='payout_requests')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1.00)])
    currency = models.CharField(max_length=3, default='USD')
    payout_method = models.CharField(max_length=20, choices=PAYOUT_METHODS)
    
    # Payout details
    recipient_details = models.JSONField(help_text="Bank account, PayPal email, etc.")
    provider_payout_id = models.CharField(max_length=200, blank=True)
    provider_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    status = models.CharField(max_length=20, choices=PAYOUT_STATUS, default='pending')
    failure_reason = models.CharField(max_length=300, blank=True)
    
    # Timestamps
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payout_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.payout_id:
            import random
            import string
            self.payout_id = 'PAYOUT-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        # Calculate net amount
        self.net_amount = self.amount - self.provider_fee
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Payout {self.payout_id} - ${self.amount}"


class Invoice(models.Model):
    """
    Invoices for orders and transactions
    """
    INVOICE_STATUS = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    
    # Parties
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='invoice')
    
    # Invoice details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')
    
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='draft')
    due_date = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Billing details
    billing_address = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            import random
            import string
            self.invoice_number = 'INV-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Calculate total
        self.total_amount = self.subtotal + self.tax_amount
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date < timezone.now() and self.status not in ['paid', 'cancelled']
