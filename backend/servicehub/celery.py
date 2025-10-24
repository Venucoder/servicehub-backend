import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'servicehub.settings.development')

app = Celery('servicehub')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'update-analytics-daily': {
        'task': 'apps.analytics.tasks.update_daily_analytics',
        'schedule': 86400.0,  # Run daily
    },
    'process-pending-payouts': {
        'task': 'apps.payments.tasks.process_pending_payouts',
        'schedule': 3600.0,  # Run hourly
    },
    'send-order-reminders': {
        'task': 'apps.orders.tasks.send_order_reminders',
        'schedule': 1800.0,  # Run every 30 minutes
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')