from django.core.management.base import BaseCommand
from subscriptions.models import Module

BASE_MODULES = [
    {"code": "academic", "name": "Académico"},
    {"code": "portal_digital", "name": "Portal Digital"},
    {"code": "administrative", "name": "Administrativo"},
    {"code": "health_wellbeing", "name": "Salud y Bienestar"},
    {"code": "payroll_rrhh", "name": "Nómina y RRHH"},
    {"code": "accounting", "name": "Módulo Contable"},
    {"code": "sales", "name": "Ventas"},
    {"code": "purchases", "name": "Compras"},
    {"code": "help", "name": "Ayuda"},
    {"code": "privacy", "name": "Privacidad"},
    {"code": "maintenance", "name": "Mantenimiento"},
    {"code": "saas_management", "name": "Gestión SaaS"},
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
