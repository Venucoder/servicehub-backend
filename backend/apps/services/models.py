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
    
    # Verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Business details
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    
    # Ratings
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
    PRICING_TYPE_CHOICES = (
        ('per_unit', 'Per Unit'),
        ('subscription', 'Subscription Only'),
        ('both', 'Both'),
    )
    
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
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPE_CHOICES)
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, help_text="e.g., bottle, kg, litre")
    minimum_order = models.IntegerField(default=1)
    
    # Availability
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    
    # Stock management
    has_stock_tracking = models.BooleanField(default=True)
    current_stock = models.IntegerField(default=0)
    
    # Business hours (NEW)
    business_hours_start = models.TimeField(default='06:00:00')
    business_hours_end = models.TimeField(default='22:00:00')
    
    # Operating days (NEW)
    operating_days = models.JSONField(
        default=list,
        help_text="Days service is available: ['monday', 'tuesday', ...]"
    )
    
    # Immediate delivery settings (NEW)
    supports_immediate_delivery = models.BooleanField(default=True)
    immediate_delivery_time = models.IntegerField(
        default=120,
        help_text="Minutes for immediate delivery (e.g., 120 = within 2 hours)"
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


class SubscriptionPackage(models.Model):
    """
    Subscription packages created by service providers
    Provider defines: 20 units @ ₹140, 30 units @ ₹210, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='subscription_packages'
    )
    
    # Package details
    name = models.CharField(
        max_length=100,
        help_text="e.g., 'Starter Pack', 'Value Pack', 'Family Pack'"
    )
    units = models.IntegerField(help_text="Total units in package")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Calculated fields
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False
    )
    savings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Savings compared to base price"
    )
    
    # Validity
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(
        default=0,
        help_text="Display order in listing (lower = shown first)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription_packages'
        ordering = ['display_order', 'units']
        indexes = [
            models.Index(fields=['service', 'is_active']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate price per unit
        if self.units > 0:
            self.price_per_unit = self.price / self.units
        
        # Auto-calculate savings vs base price
        if self.service:
            base_total = self.service.base_price * self.units
            self.savings = base_total - self.price
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.service.name} - {self.name} ({self.units} units)"


class Subscription(models.Model):
    """
    Customer subscriptions - unit-based, flexible usage
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    DELIVERY_TYPE = (
        ('self_pickup', 'Self Pickup'),
        ('auto_delivery', 'Auto Delivery'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    package = models.ForeignKey(
        SubscriptionPackage,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    
    # Subscription details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPE)
    
    # Unit tracking (CORE FEATURE)
    total_units = models.IntegerField()
    used_units = models.IntegerField(default=0)
    remaining_units = models.IntegerField()
    
    # Pricing
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    per_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Auto-delivery settings (only if delivery_type = 'auto_delivery')
    delivery_address = models.TextField(blank=True, null=True)
    preferred_time = models.TimeField(blank=True, null=True)
    delivery_days = models.JSONField(
        default=list,
        blank=True,
        help_text="Days for auto-delivery: ['monday', 'wednesday', 'friday']"
    )
    units_per_delivery = models.IntegerField(
        default=1,
        help_text="Units to deliver each time"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['package']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate remaining units
        self.remaining_units = self.total_units - self.used_units
        
        # Auto-complete if all units used
        if self.remaining_units == 0 and self.status == 'active':
            self.status = 'completed'
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def use_units(self, quantity=1):
        """Mark units as used"""
        if self.status != 'active':
            return False, "Subscription is not active"
        
        if self.remaining_units < quantity:
            return False, f"Not enough units. Only {self.remaining_units} remaining"
        
        self.used_units += quantity
        self.save()
        return True, "Units marked as used"
    
    def pause(self):
        """Pause subscription"""
        if self.status == 'active':
            self.status = 'paused'
            self.paused_at = timezone.now()
            self.save()
            return True
        return False
    
    def resume(self):
        """Resume subscription"""
        if self.status == 'paused' and self.remaining_units > 0:
            self.status = 'active'
            self.paused_at = None
            self.save()
            return True
        return False
    
    def cancel(self):
        """Cancel subscription"""
        if self.status in ['active', 'paused']:
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.save()
            return True
        return False
    
    def __str__(self):
        return f"{self.customer.username} - {self.package.service.name} ({self.remaining_units}/{self.total_units})"


class SubscriptionUsage(models.Model):
    """
    Track each time customer uses units from subscription
    Digital punch card system
    """
    USAGE_TYPE = (
        ('pickup', 'Self Pickup'),
        ('delivered', 'Delivered'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='usage_history'
    )
    
    units_used = models.IntegerField(default=1)
    usage_type = models.CharField(max_length=20, choices=USAGE_TYPE)
    
    # For pickups
    picked_up_at = models.DateTimeField(null=True, blank=True)
    
    # For deliveries
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries_made'
    )
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'subscription_usage'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.subscription.customer.username} - {self.units_used} units ({self.usage_type})"