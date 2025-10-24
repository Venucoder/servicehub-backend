from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class UserActivity(models.Model):
    """
    Track user activities and engagement
    """
    ACTIVITY_TYPES = (
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('profile_update', 'Profile Update'),
        ('service_view', 'Service View'),
        ('service_create', 'Service Create'),
        ('service_update', 'Service Update'),
        ('order_create', 'Order Create'),
        ('order_update', 'Order Update'),
        ('message_send', 'Message Send'),
        ('payment_made', 'Payment Made'),
        ('review_create', 'Review Create'),
        ('search', 'Search'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=300)
    
    # Related objects
    service_id = models.UUIDField(null=True, blank=True)
    order_id = models.UUIDField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type}"


class ServiceAnalytics(models.Model):
    """
    Daily analytics for services
    """
    service = models.ForeignKey('services.Service', on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    
    # View metrics
    views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    inquiries = models.PositiveIntegerField(default=0)
    orders = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Revenue metrics
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Performance metrics
    avg_response_time = models.DurationField(null=True, blank=True)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_analytics'
        unique_together = ['service', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['service']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.service.title} - {self.date}"


class UserAnalytics(models.Model):
    """
    Daily analytics for users
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    
    # Activity metrics
    login_count = models.PositiveIntegerField(default=0)
    session_duration = models.DurationField(null=True, blank=True)
    page_views = models.PositiveIntegerField(default=0)
    
    # Business metrics (for providers)
    orders_received = models.PositiveIntegerField(default=0)
    orders_completed = models.PositiveIntegerField(default=0)
    revenue_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Customer metrics
    orders_placed = models.PositiveIntegerField(default=0)
    amount_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_analytics'
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"


class PlatformAnalytics(models.Model):
    """
    Daily platform-wide analytics
    """
    date = models.DateField(unique=True)
    
    # User metrics
    new_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    total_users = models.PositiveIntegerField(default=0)
    
    # Service metrics
    new_services = models.PositiveIntegerField(default=0)
    active_services = models.PositiveIntegerField(default=0)
    total_services = models.PositiveIntegerField(default=0)
    
    # Order metrics
    new_orders = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)
    
    # Revenue metrics
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    platform_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Performance metrics
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    customer_satisfaction = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'platform_analytics'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"Platform Analytics - {self.date}"


class SearchAnalytics(models.Model):
    """
    Track search queries and results
    """
    query = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='searches', null=True, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    clicked_service_id = models.UUIDField(null=True, blank=True)
    click_position = models.PositiveIntegerField(null=True, blank=True)
    
    # Context
    category = models.CharField(max_length=100, blank=True)
    filters_applied = models.JSONField(default=dict, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'search_analytics'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['query']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Search: {self.query}"


class RevenueReport(models.Model):
    """
    Monthly revenue reports
    """
    REPORT_TYPES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Revenue breakdown
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    platform_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_processing_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Volume metrics
    total_orders = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    cancelled_orders = models.PositiveIntegerField(default=0)
    
    # Category breakdown
    category_breakdown = models.JSONField(default=dict, blank=True)
    
    # Growth metrics
    growth_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'revenue_reports'
        unique_together = ['report_type', 'period_start', 'period_end']
        ordering = ['-period_start']
    
    def __str__(self):
        return f"{self.get_report_type_display()} Report - {self.period_start} to {self.period_end}"
