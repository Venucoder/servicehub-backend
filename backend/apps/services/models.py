from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import uuid

User = get_user_model()


class ServiceCategory(models.Model):
    """
    Categories for organizing services (e.g., Web Development, Graphic Design, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_categories'
        verbose_name_plural = 'Service Categories'
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Service(models.Model):
    """
    Main service model representing services offered by providers
    """
    SERVICE_STATUS = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('inactive', 'Inactive'),
    )
    
    DELIVERY_TIME_UNITS = (
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, help_text="Brief description for listings")
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1.00)])
    currency = models.CharField(max_length=3, default='USD')
    
    # Delivery
    delivery_time = models.PositiveIntegerField()
    delivery_time_unit = models.CharField(max_length=10, choices=DELIVERY_TIME_UNITS, default='days')
    
    # Service details
    requirements = models.TextField(help_text="What you need from the buyer to start")
    what_you_get = models.TextField(help_text="What the buyer will receive")
    
    # Media
    featured_image = models.ImageField(upload_to='services/images/', blank=True, null=True)
    gallery_images = models.JSONField(default=list, blank=True, help_text="List of additional image URLs")
    video_url = models.URLField(blank=True, null=True)
    
    # Status and metrics
    status = models.CharField(max_length=20, choices=SERVICE_STATUS, default='draft')
    views_count = models.PositiveIntegerField(default=0)
    orders_count = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(5)])
    reviews_count = models.PositiveIntegerField(default=0)
    
    # SEO
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'services'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Service.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def delivery_time_display(self):
        return f"{self.delivery_time} {self.delivery_time_unit}"


class ServicePackage(models.Model):
    """
    Different packages/tiers for a service (Basic, Standard, Premium)
    """
    PACKAGE_TYPES = (
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    )
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='packages')
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1.00)])
    delivery_time = models.PositiveIntegerField()
    delivery_time_unit = models.CharField(max_length=10, choices=Service.DELIVERY_TIME_UNITS, default='days')
    features = models.JSONField(default=list, help_text="List of features included")
    revisions = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'service_packages'
        unique_together = ['service', 'package_type']
        ordering = ['service', 'price']
    
    def __str__(self):
        return f"{self.service.title} - {self.name}"


class ServiceReview(models.Model):
    """
    Reviews and ratings for services
    """
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_reviews')
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='review')
    
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    
    # Detailed ratings
    communication_rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    service_quality_rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    delivery_time_rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    is_featured = models.BooleanField(default=False)
    provider_response = models.TextField(blank=True)
    provider_response_date = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_reviews'
        ordering = ['-created_at']
        unique_together = ['service', 'customer', 'order']
        indexes = [
            models.Index(fields=['service']),
            models.Index(fields=['customer']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Review for {self.service.title} by {self.customer.username}"


class ServiceFAQ(models.Model):
    """
    Frequently Asked Questions for services
    """
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'service_faqs'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"FAQ: {self.question[:50]}..."
