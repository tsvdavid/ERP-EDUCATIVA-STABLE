from django.core.management.base import BaseCommand
from subscriptions.models import Module

BASE_MODULES = [
    {"code": "users", "name": "Usuarios"},
    {"code": "academic", "name": "Academia"},
    {"code": "treasury", "name": "Tesorería"},
    {"code": "accounting", "name": "Contabilidad"},
    {"code": "learning", "name": "Aprendizaje"},
    {"code": "communication", "name": "Comunicación"},
    {"code": "subscriptions", "name": "Suscripciones"},
]

class Command(BaseCommand):
    help = "Populate base ERP modules (idempotent)."

    def handle(self, *args, **options):
        created_count = 0
        for mod in BASE_MODULES:
            obj, created = Module.objects.get_or_create(
                code=mod["code"], defaults={"name": mod["name"]}
            )
            if created:
                created_count += 1
        self.stdout.write(self.style.SUCCESS(
            f"Modules ensured. Created {created_count} new entries. Total now: {Module.objects.count()}"
        ))
