from django.core.management.base import BaseCommand
from subscriptions.models import Subscription, Module, SubscriptionModule

class Command(BaseCommand):
    help = "Assign all existing modules to each ACTIVE subscription (idempotent)."

    def handle(self, *args, **options):
        active_subs = Subscription.objects.filter(status='ACTIVE')
        modules = list(Module.objects.all())
        total_created = 0
        for sub in active_subs:
            existing_module_ids = set(SubscriptionModule.objects.filter(subscription=sub).values_list('module_id', flat=True))
            for mod in modules:
                if mod.id not in existing_module_ids:
                    SubscriptionModule.objects.create(subscription=sub, module=mod)
                    total_created += 1
        self.stdout.write(self.style.SUCCESS(f"Linked modules to subscriptions. Created {total_created} new SubscriptionModule entries."))
