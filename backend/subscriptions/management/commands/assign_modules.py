from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Deprecated: module enablement is plan-based and no longer linked per subscription."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "No action executed: module enablement now comes from each plan's included_modules."
            )
        )
