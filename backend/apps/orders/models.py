from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
import uuid

User = get_user_model()


class Order(models.Model):
    """
    Main order model for service purchases
    """
    ORDER_STATUS = (
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('in_progress', 'In Progress'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('disputed', 'Disputed'),
    )
    
    PRIORITY_LEVELS = (
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Parties
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_orders')
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='provider_orders')
    
    # Service details
    service = models.ForeignKey('services.Service', on_delete=models.CASCADE, related_name='orders')
    package = models.ForeignKey('services.ServicePackage', on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    
    # Order details
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField(help_text="Customer requirements and details")
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    extras_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')
    
    # Timeline
    delivery_date = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Status and priority
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    
    # Communication
    last_activity = models.DateTimeField(auto_now=True)
    unread_messages_customer = models.PositiveIntegerField(default=0)
    unread_messages_provider = models.PositiveIntegerField(default=0)
    
    # Metadata
    is_rush_order = models.BooleanField(default=False)
    rush_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['provider']),
            models.Index(fields=['service']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['delivery_date']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            import random
            import string
            self.order_number = 'ORD-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        # Calculate total price
        self.total_price = self.base_price + self.extras_price + self.rush_fee
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order {self.order_number} - {self.title}"
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.delivery_date < timezone.now() and self.status not in ['completed', 'cancelled', 'refunded']


class OrderExtra(models.Model):
    """
    Additional services/extras added to an order
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='extras')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    delivery_time_extension = models.PositiveIntegerField(default=0, help_text="Additional days needed")
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_extras'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Extra: {self.title} for {self.order.order_number}"


class OrderMessage(models.Model):
    """
    Messages between customer and provider for an order
    """
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('file', 'File'),
        ('system', 'System'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    file_attachment = models.FileField(upload_to='order_messages/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['sender']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} in {self.order.order_number}"


class OrderDeliverable(models.Model):
    """
    Files and deliverables submitted by the provider
    """
    DELIVERABLE_STATUS = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('revision_requested', 'Revision Requested'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='deliverables')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='order_deliverables/')
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=DELIVERABLE_STATUS, default='pending')
    revision_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'order_deliverables'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Deliverable: {self.title} for {self.order.order_number}"


class OrderRevision(models.Model):
    """
    Revision requests for orders
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='revisions')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    details = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_revisions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Revision for {self.order.order_number}"


class OrderTimeline(models.Model):
    """
    Timeline/activity log for orders
    """
    ACTION_TYPES = (
        ('created', 'Order Created'),
        ('paid', 'Payment Received'),
        ('started', 'Work Started'),
        ('message_sent', 'Message Sent'),
        ('deliverable_uploaded', 'Deliverable Uploaded'),
        ('revision_requested', 'Revision Requested'),
        ('delivered', 'Order Delivered'),
        ('completed', 'Order Completed'),
        ('cancelled', 'Order Cancelled'),
        ('refunded', 'Order Refunded'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='timeline')
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.CharField(max_length=300)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_timeline'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number}: {self.action}"
