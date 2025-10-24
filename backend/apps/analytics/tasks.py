from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from django.contrib.auth import get_user_model
from .models import PlatformAnalytics, UserAnalytics, ServiceAnalytics
from apps.services.models import Service
from apps.orders.models import Order
from apps.payments.models import Transaction
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def update_daily_analytics():
    """
    Update daily analytics for platform, users, and services
    """
    today = timezone.now().date()
    
    try:
        # Update platform analytics
        update_platform_analytics(today)
        
        # Update user analytics
        update_user_analytics(today)
        
        # Update service analytics
        update_service_analytics(today)
        
        logger.info(f"Daily analytics updated successfully for {today}")
        
    except Exception as e:
        logger.error(f"Error updating daily analytics: {e}")
        raise


def update_platform_analytics(date):
    """Update platform-wide analytics"""
    
    # Get or create platform analytics for the date
    platform_analytics, created = PlatformAnalytics.objects.get_or_create(
        date=date,
        defaults={
            'new_users': 0,
            'active_users': 0,
            'total_users': 0,
            'new_services': 0,
            'active_services': 0,
            'total_services': 0,
            'new_orders': 0,
            'completed_orders': 0,
            'total_orders': 0,
            'gross_revenue': 0,
            'net_revenue': 0,
            'platform_fees': 0,
            'avg_order_value': 0,
            'customer_satisfaction': 0,
        }
    )
    
    # Calculate metrics
    platform_analytics.new_users = User.objects.filter(created_at__date=date).count()
    platform_analytics.total_users = User.objects.count()
    
    platform_analytics.new_services = Service.objects.filter(created_at__date=date).count()
    platform_analytics.active_services = Service.objects.filter(status='active').count()
    platform_analytics.total_services = Service.objects.count()
    
    platform_analytics.new_orders = Order.objects.filter(created_at__date=date).count()
    platform_analytics.completed_orders = Order.objects.filter(
        completed_at__date=date
    ).count()
    platform_analytics.total_orders = Order.objects.count()
    
    # Revenue calculations
    daily_transactions = Transaction.objects.filter(
        created_at__date=date,
        status='completed',
        transaction_type='payment'
    )
    
    platform_analytics.gross_revenue = daily_transactions.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    platform_analytics.platform_fees = daily_transactions.aggregate(
        total=Sum('platform_fee')
    )['total'] or 0
    
    platform_analytics.net_revenue = platform_analytics.gross_revenue - platform_analytics.platform_fees
    
    # Average order value
    if platform_analytics.new_orders > 0:
        platform_analytics.avg_order_value = platform_analytics.gross_revenue / platform_analytics.new_orders
    
    platform_analytics.save()


def update_user_analytics(date):
    """Update user analytics"""
    
    # Get active users for the date
    active_users = User.objects.filter(
        last_login__date=date
    )
    
    for user in active_users:
        user_analytics, created = UserAnalytics.objects.get_or_create(
            user=user,
            date=date,
            defaults={
                'login_count': 0,
                'page_views': 0,
                'orders_received': 0,
                'orders_completed': 0,
                'revenue_earned': 0,
                'orders_placed': 0,
                'amount_spent': 0,
            }
        )
        
        # Calculate user-specific metrics
        if user.role == 'provider':
            user_analytics.orders_received = Order.objects.filter(
                provider=user,
                created_at__date=date
            ).count()
            
            user_analytics.orders_completed = Order.objects.filter(
                provider=user,
                completed_at__date=date
            ).count()
            
            user_analytics.revenue_earned = Transaction.objects.filter(
                user=user,
                created_at__date=date,
                transaction_type='payment',
                status='completed'
            ).aggregate(total=Sum('net_amount'))['total'] or 0
        
        elif user.role == 'customer':
            user_analytics.orders_placed = Order.objects.filter(
                customer=user,
                created_at__date=date
            ).count()
            
            user_analytics.amount_spent = Transaction.objects.filter(
                user=user,
                created_at__date=date,
                transaction_type='payment',
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
        
        user_analytics.save()


def update_service_analytics(date):
    """Update service analytics"""
    
    # Get services that had activity on this date
    active_services = Service.objects.filter(
        created_at__lte=date
    )
    
    for service in active_services:
        service_analytics, created = ServiceAnalytics.objects.get_or_create(
            service=service,
            date=date,
            defaults={
                'views': 0,
                'unique_views': 0,
                'inquiries': 0,
                'orders': 0,
                'conversion_rate': 0,
                'revenue': 0,
                'completion_rate': 0,
            }
        )
        
        # Calculate service metrics
        service_analytics.orders = Order.objects.filter(
            service=service,
            created_at__date=date
        ).count()
        
        service_analytics.revenue = Order.objects.filter(
            service=service,
            created_at__date=date,
            status__in=['completed', 'delivered']
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        # Calculate completion rate
        total_orders = Order.objects.filter(service=service).count()
        completed_orders = Order.objects.filter(
            service=service,
            status='completed'
        ).count()
        
        if total_orders > 0:
            service_analytics.completion_rate = (completed_orders / total_orders) * 100
        
        service_analytics.save()


@shared_task
def generate_monthly_report(year, month):
    """
    Generate monthly analytics report
    """
    try:
        from .models import RevenueReport
        from datetime import date
        import calendar
        
        # Calculate period
        period_start = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        period_end = date(year, month, last_day)
        
        # Get or create report
        report, created = RevenueReport.objects.get_or_create(
            report_type='monthly',
            period_start=period_start,
            period_end=period_end,
            defaults={
                'gross_revenue': 0,
                'platform_fees': 0,
                'payment_processing_fees': 0,
                'refunds': 0,
                'net_revenue': 0,
                'total_orders': 0,
                'completed_orders': 0,
                'cancelled_orders': 0,
                'category_breakdown': {},
                'growth_rate': 0,
            }
        )
        
        # Calculate metrics
        monthly_transactions = Transaction.objects.filter(
            created_at__date__range=[period_start, period_end],
            status='completed'
        )
        
        report.gross_revenue = monthly_transactions.filter(
            transaction_type='payment'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        report.platform_fees = monthly_transactions.aggregate(
            total=Sum('platform_fee')
        )['total'] or 0
        
        report.payment_processing_fees = monthly_transactions.aggregate(
            total=Sum('provider_fee')
        )['total'] or 0
        
        report.refunds = monthly_transactions.filter(
            transaction_type='refund'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        report.net_revenue = (
            report.gross_revenue - 
            report.platform_fees - 
            report.payment_processing_fees - 
            report.refunds
        )
        
        # Order metrics
        monthly_orders = Order.objects.filter(
            created_at__date__range=[period_start, period_end]
        )
        
        report.total_orders = monthly_orders.count()
        report.completed_orders = monthly_orders.filter(status='completed').count()
        report.cancelled_orders = monthly_orders.filter(status='cancelled').count()
        
        report.save()
        
        logger.info(f"Monthly report generated for {year}-{month}")
        
    except Exception as e:
        logger.error(f"Error generating monthly report: {e}")
        raise