# backend/apps/services/models.py
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class ServiceCategory(models.Model):
    """Categories for different types of services"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_categories'
        verbose_name_plural = 'Service Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ServiceProvider(models.Model):
    """Service providers who offer services"""
    STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('rejected', 'Rejected'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_provider'
    )
    business_name = models.CharField(max_length=255)
    business_address = models.TextField()
    business_phone = models.CharField(max_length=15)
    business_email = models.EmailField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_ratings = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_providers'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.business_name}"


class Service(models.Model):
    """Individual services offered by providers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='services'
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name='services'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Price per unit (e.g., ₹10 per can)"
    )
    unit = models.CharField(
        max_length=50, 
        help_text="e.g., can, liter, piece, kg"
    )
    
    # Quantity options for one-time orders
    quantity_options = models.JSONField(
        default=list,
        blank=True,
        help_text='Example: [{"label": "250ml", "value": 0.25, "price": 15}, {"label": "1 Liter", "value": 1, "price": 60}]'
    )
    
    minimum_order = models.IntegerField(default=1)
    
    # Availability
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    
    # Stock management
    has_stock_tracking = models.BooleanField(default=True)
    current_stock = models.IntegerField(default=0)
    
    # Business hours
    business_hours_start = models.TimeField(default='06:00:00')
    business_hours_end = models.TimeField(default='22:00:00')
    operating_days = models.JSONField(
        default=list,
        help_text='["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]'
    )
    
    # Delivery options
    supports_immediate_delivery = models.BooleanField(
        default=True,
        help_text="Can customers order for immediate delivery?"
    )
    immediate_delivery_time = models.IntegerField(
        default=120,
        help_text="Expected delivery time in minutes (e.g., 120 = 2 hours)"
    )
    
    # Feature flags
    supports_prepaid_cards = models.BooleanField(
        default=True,
        help_text="Does this service support prepaid cards?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'services'
        indexes = [
            models.Index(fields=['provider', 'is_active']),
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.provider.business_name}"


class PrepaidCardOption(models.Model):
    """
    Prepaid card options - like buying a physical punch card
    Example: "30-can water card for ₹270"
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='prepaid_card_options'
    )
    
    # Card details
    name = models.CharField(
        max_length=100,
        help_text="e.g., 'Starter Pack', '30-Can Card', 'Monthly Card'"
    )
    total_units = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total units in card (e.g., 30 cans, 30 liters, 50 pieces)"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total price for the card"
    )
    
    # Auto-calculated fields
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        help_text="Calculated: price / total_units"
    )
    savings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Savings compared to base price"
    )
    
    # Display
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(
        default=0,
        help_text="Display order in listing (lower = shown first)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prepaid_card_options'
        ordering = ['service', 'display_order', 'total_units']
        indexes = [
            models.Index(fields=['service', 'is_active']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate price per unit
        if self.total_units > 0:
            self.price_per_unit = self.price / self.total_units
        
        # Auto-calculate savings
        if self.service:
            base_total = self.service.base_price * self.total_units
            self.savings = base_total - self.price
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.service.name} - {self.name} ({self.total_units} units)"


class PrepaidCard(models.Model):
    """
    Digital prepaid card owned by customer
    Like physical punch card with 30 boxes
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('exhausted', 'Exhausted'),  # All units used
        ('cancelled', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prepaid_cards'
    )
    card_option = models.ForeignKey(
        PrepaidCardOption,
        on_delete=models.PROTECT,
        related_name='issued_cards'
    )
    
    # Card details
    total_units = models.DecimalField(max_digits=10, decimal_places=2)
    used_units = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_units = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Pricing
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    per_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Timestamps
    purchased_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    exhausted_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'prepaid_cards'
        ordering = ['-purchased_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['card_option']),
            models.Index(fields=['purchased_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate remaining units
        self.remaining_units = self.total_units - self.used_units
        
        # Auto-update status if exhausted
        if self.remaining_units <= 0 and self.status == 'active':
            self.status = 'exhausted'
            self.exhausted_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def use_units(self, quantity):
        """Mark units as used - like punching boxes on physical card"""
        if self.status != 'active':
            return False, f"Card is {self.status}"
        
        if self.remaining_units < quantity:
            return False, f"Not enough units. Only {self.remaining_units} remaining"
        
        self.used_units += quantity
        self.last_used_at = timezone.now()
        self.save()
        return True, "Units marked as used"
    
    def cancel(self):
        """Cancel the card"""
        if self.status == 'active':
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.save()
            return True
        return False
    
    def __str__(self):
        return f"{self.customer.username} - {self.card_option.service.name} ({self.remaining_units}/{self.total_units})"


class CardUsage(models.Model):
    """
    Track each usage of prepaid card
    Like marking a box on physical punch card with date
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card = models.ForeignKey(
        PrepaidCard,
        on_delete=models.CASCADE,
        related_name='usage_history'
    )
    
    # Usage details
    units_used = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="How many units were used (e.g., 1 can, 0.5 liter, 3 pieces)"
    )
    
    # Who marked it
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='marked_card_usages',
        help_text="Vendor who marked the card"
    )
    
    # When & where
    used_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(
        blank=True,
        help_text="e.g., 'Picked up at shop', 'Delivered to home'"
    )
    
    class Meta:
        db_table = 'card_usage'
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['card', 'used_at']),
        ]
    
    def __str__(self):
        return f"{self.card.customer.username} - Used {self.units_used} units on {self.used_at.date()}"