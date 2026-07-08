import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from users.models import Institution
from .models import Subscription, GlobalSettings

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Institution)
def create_institution_subscription(sender, instance, created, **kwargs):
    if created:
        settings, _ = GlobalSettings.objects.get_or_create(id=1)
        default_plan = settings.default_plan if settings and settings.default_plan and settings.default_plan.is_active else None
        if settings and settings.default_plan and not settings.default_plan.is_active:
            logger.warning(
                "GlobalSettings.default_plan is inactive; creating subscription without plan",
                extra={'institution_id': instance.id, 'plan_id': settings.default_plan_id}
            )
        if not default_plan:
            logger.warning(
                "No default SaaS plan configured; creating subscription without plan",
                extra={'institution_id': instance.id}
            )
        
        # Create subscription even if plan is missing to preserve existing flow.
        Subscription.objects.create(
            institution=instance,
            plan=default_plan,
            status='ACTIVE',
            start_date=timezone.now().date(),
            next_billing_date=timezone.now().date() + timedelta(days=30),
            monthly_fee=default_plan.base_price_monthly if default_plan else 0.00
        )
