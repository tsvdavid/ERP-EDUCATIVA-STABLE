from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from users.models import Institution
from .models import Subscription, Plan

@receiver(post_save, sender=Institution)
def create_institution_subscription(sender, instance, created, **kwargs):
    if created:
        # 1. Try to find a default plan (e.g. named 'Trial' or first active plan)
        default_plan = Plan.objects.filter(is_active=True).first()
        
        # 2. Create subscription
        Subscription.objects.create(
            institution=instance,
            plan=default_plan,
            status='ACTIVE',
            start_date=timezone.now().date(),
            next_billing_date=timezone.now().date() + timedelta(days=30),
            monthly_fee=default_plan.base_price_monthly if default_plan else 0.00
        )
