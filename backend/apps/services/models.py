import uuid
from django.db import models
from django.conf import settings

class ServiceCategory(models.Model):
    """
    Categories for different types of services
    (Water, Milk, Grocery, Laundry, etc.)
    """
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
    """
    Service providers who offer services to customers
    """
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
        return f"{self.business_name} - {self.user.username}"


class Service(models.Model):
    """
    Individual services offered by providers
    """
    PRICING_TYPE_CHOICES = (
        ('per_unit', 'Per Unit'),
        ('subscription', 'Subscription'),
        ('bulk', 'Bulk Discount'),
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
    subscription_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly subscription price"
    )
    
    # Service details
    unit = models.CharField(max_length=50, help_text="e.g., bottle, kg, litre")
    minimum_order = models.IntegerField(default=1)
    
    # Availability
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    
    # Stock management
    has_stock_tracking = models.BooleanField(default=True)
    current_stock = models.IntegerField(default=0)
    
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


class Subscription(models.Model):
    """
    Customer subscriptions for services (like monthly water card)
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    
    # Subscription details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Usage tracking (like card boxes)
    total_units = models.IntegerField(help_text="Total units in subscription (e.g., 30 for monthly)")
    used_units = models.IntegerField(default=0)
    remaining_units = models.IntegerField()
    
    # Pricing
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    per_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Auto-renewal
    auto_renew = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['service', 'status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.customer.username} - {self.service.name}"
    
    def save(self, *args, **kwargs):
        self.remaining_units = self.total_units - self.used_units
        super().save(*args, **kwargs)