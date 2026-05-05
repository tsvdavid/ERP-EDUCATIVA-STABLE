import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.core import serializers

class Command(BaseCommand):
    help = 'Restaura datos de una institución desde un volcado JSON de forma atómica.'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='Ruta al archivo de volcado (JSON)')
        parser.add_argument('--dry-run', action='store_true', help='Simula la restauración sin persistir cambios')

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']

        if not os.path.exists(file_path):
            raise CommandError(f"El archivo {file_path} no existe.")

        self.stdout.write(self.style.SUCCESS(f"📥 Iniciando restauración desde: {file_path}"))
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️ MODO DRY-RUN: Los cambios no se guardarán."))

        try:
            with transaction.atomic():
                # Desactivar RLS temporalmente para la sesión administrativa de restauración
                # O simplemente confiar en que el restore corre con privilegios
                with connection.cursor() as cursor:
                    cursor.execute("SET app.current_tenant = '0';") # Modo administración
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    objects = serializers.deserialize("json", f)
                    
                    count = 0
                    for obj in objects:
                        if not dry_run:
                            obj.save()
                        count += 1
                    
                    if dry_run:
                        self.stdout.write(self.style.SUCCESS(f"✅ Simulación completada. {count} objetos validados."))
                        # Provocamos un rollback manual en dry-run
                        transaction.set_rollback(True)
                    else:
                        self.stdout.write(self.style.SUCCESS(f"✅ Restauración exitosa. {count} objetos procesados."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error durante la restauración: {e}"))
            raise CommandError("La restauración falló y se realizó un rollback automático.")
