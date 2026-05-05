import os
from celery import Celery
from core.celery_base import TenantAwareTask

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config', task_cls=TenantAwareTask)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

from celery.schedules import crontab

app.conf.beat_schedule = {
    'daily-subscription-check': {
        'task': 'subscriptions.tasks.daily_subscription_check',
        'schedule': crontab(minute=0, hour=0),
    },
    'capture-daily-kpis': {
        'task': 'subscriptions.tasks.capture_daily_kpis',
        'schedule': crontab(minute=0, hour=1),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
