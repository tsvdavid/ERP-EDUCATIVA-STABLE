from django.core.management.base import BaseCommand
from users.models import Institution
from subscriptions.models import Subscription, Plan
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Backfill subscriptions for institutions without one'

    def handle(self, *args, **options):
        institutions = Institution.objects.filter(subscription__isnull=True)
        default_plan = Plan.objects.filter(is_active=True).first()
        
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
