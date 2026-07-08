import logging
from django.core.management.base import BaseCommand
from users.models import Institution
from subscriptions.models import Subscription, GlobalSettings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Backfill subscriptions for institutions without one'

    def handle(self, *args, **options):
        institutions = Institution.objects.filter(subscription__isnull=True)
        settings, _ = GlobalSettings.objects.get_or_create(id=1)
        default_plan = settings.default_plan if settings and settings.default_plan and settings.default_plan.is_active else None

        if settings and settings.default_plan and not settings.default_plan.is_active:
            warning_msg = 'GlobalSettings.default_plan está inactivo; se crearán suscripciones sin plan.'
            logger.warning(warning_msg)
            self.stdout.write(self.style.WARNING(warning_msg))
        if not default_plan:
            warning_msg = 'No existe plan predeterminado SaaS configurado; se crearán suscripciones sin plan.'
            logger.warning(warning_msg)
            self.stdout.write(self.style.WARNING(warning_msg))
        
        count = 0
        for inst in institutions:
            Subscription.objects.create(
                institution=inst,
                plan=default_plan,
                status='ACTIVE',
                start_date=timezone.now().date(),
                next_billing_date=timezone.now().date() + timedelta(days=30),
                monthly_fee=default_plan.base_price_monthly if default_plan else 0.00
            )
            count += 1
            self.stdout.write(self.style.SUCCESS(f'Created subscription for {inst.name}'))
            
        self.stdout.write(self.style.SUCCESS(f'Successfully backfilled {count} institutions.'))
