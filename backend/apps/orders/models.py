import uuid
from django.db import models
from django.conf import settings
from apps.services.models import Service, Subscription


class Order(models.Model):
    """
    Orders placed by customers for services
    """
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    ORDER_TYPE = (
        ('one_time', 'One Time Purchase'),
        ('subscription', 'Subscription'),
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
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Link to subscription if this is a subscription order"
    )
    
    # Order details
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Delivery details
    delivery_address = models.TextField()
    delivery_date = models.DateField(null=True, blank=True)
    delivery_time_slot = models.CharField(max_length=50, blank=True)
    
    # Additional info
    notes = models.TextField(blank=True, help_text="Customer notes or special instructions")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['service', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'delivery_date']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.customer.username}"
    
    def save(self, *args, **kwargs):
        # Generate order number if not exists
        if not self.order_number:
            import datetime
            date_str = datetime.datetime.now().strftime('%Y%m%d')
            # Format: ORD20250125001
            last_order = Order.objects.filter(
                order_number__startswith=f'ORD{date_str}'
            ).order_by('-order_number').first()
            
            if last_order:
                last_number = int(last_order.order_number[-3:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.order_number = f'ORD{date_str}{new_number:03d}'
        
        super().save(*args, **kwargs)


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
    
    def __str__(self):
        return f"{self.service.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


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
    
    def __str__(self):
        return f"{self.order.order_number}: {self.from_status} → {self.to_status}"