import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.services.models import Service, Subscription


class Order(models.Model):
    """
    One-time orders placed by customers
    """
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('out_for_delivery', 'Out for Delivery'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    ORDER_TYPE = (
        ('one_time', 'One Time Purchase'),
    )
    
    DELIVERY_TYPE = (
        ('immediate', 'Immediate Delivery'),
        ('scheduled', 'Scheduled Delivery'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # Relationships
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    
    # Order details
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE, default='one_time')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Delivery details (UPDATED)
    delivery_type = models.CharField(
        max_length=20,
        choices=DELIVERY_TYPE,
        default='scheduled',
        help_text="Immediate (within hours) or Scheduled (future date/time)"
    )
    delivery_address = models.TextField()
    
    # For scheduled delivery
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    
    # For immediate delivery
    expected_delivery_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Expected delivery time for immediate orders"
    )
    
    # Additional info
    notes = models.TextField(blank=True, help_text="Customer notes or special instructions")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['service', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'scheduled_date']),
            models.Index(fields=['delivery_type', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        # Generate order number if not exists
        if not self.order_number:
            import datetime
            date_str = datetime.datetime.now().strftime('%Y%m%d')
            # Format: ORD20250127001
            last_order = Order.objects.filter(
                order_number__startswith=f'ORD{date_str}'
            ).order_by('-order_number').first()
            
            if last_order:
                last_number = int(last_order.order_number[-3:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.order_number = f'ORD{date_str}{new_number:03d}'
        
        # Set expected delivery time for immediate orders
        if self.delivery_type == 'immediate' and not self.expected_delivery_time:
            # Get immediate delivery time from service (default 120 minutes)
            delivery_minutes = getattr(self.service, 'immediate_delivery_time', 120)
            self.expected_delivery_time = timezone.now() + timezone.timedelta(minutes=delivery_minutes)
        
        super().save(*args, **kwargs)
    
    def confirm(self):
        """Confirm order"""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.confirmed_at = timezone.now()
            self.save()
            return True
        return False
    
    def complete(self):
        """Mark order as completed"""
        if self.status in ['confirmed', 'processing', 'out_for_delivery']:
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
            return True
        return False
    
    def cancel(self):
        """Cancel order"""
        if self.status in ['pending', 'confirmed']:
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.save()
            return True
        return False
    
    def __str__(self):
        return f"Order {self.order_number} - {self.customer.username}"


class OrderItem(models.Model):
    """
    Individual items in an order (for future multi-item orders)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT
    )
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_items'
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.service.name} x {self.quantity}"


class OrderStatusHistory(models.Model):
    """
    Track order status changes for transparency
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_status_history'
        ordering = ['-created_at']
        verbose_name_plural = 'Order Status Histories'
        indexes = [
            models.Index(fields=['order', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number}: {self.from_status} → {self.to_status}"