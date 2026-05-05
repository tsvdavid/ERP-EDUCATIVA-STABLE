import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.core import serializers
from django.db import connection, transaction
from users.models import Institution, User
from core.models import TenantModel

class Command(BaseCommand):
    help = 'Exporta datos de una única institución con integridad total y soporte multiformato.'

    def add_arguments(self, parser):
        parser.add_argument('--id', type=int, required=True, help='ID de la institución a exportar')
        parser.add_argument('--format', type=str, choices=['json', 'sql'], default='json', help='Formato de salida (json/sql)')
        parser.add_argument('--include-users', action='store_true', help='Incluir usuarios vinculados a la institución')
        parser.add_argument('--output', type=str, help='Ruta de salida personalizada')

    def handle(self, *args, **options):
        inst_id = options['id']
        fmt = options['format']
        include_users = options['include_users']
        
        try:
            institution = Institution.objects.get(id=inst_id)
        except Institution.DoesNotExist:
            raise CommandError(f"La institución con ID {inst_id} no existe.")

        self.stdout.write(self.style.SUCCESS(f"🚀 Iniciando Hardening Dump 2.0 para: {institution.name}"))

        # Preparar ruta
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = 'sql' if fmt == 'sql' else 'json'
        output_path = options['output'] or os.path.join('backups', 'tenants', f"tenant_{inst_id}_{timestamp}.{ext}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 0. Contexto RLS (Asegurar que podemos leer los datos)
        # Seteamos el tenant en la sesión por si acaso el usuario que ejecuta el comando está restringido
        with connection.cursor() as cursor:
            cursor.execute(f"SET app.current_tenant = '{inst_id}';")

        # 1. Recolección de Modelos (Orden Topológico Sugerido)
        # Definimos un orden base para respetar dependencias principales
        all_objects = []
        
        # Primero la institución (raíz)
        all_objects.extend(Institution.objects.filter(id=inst_id))
        
        # Usuarios (si se solicita)
        if include_users:
            self.stdout.write("  - Recolectando identidad (Users & Profiles)...")
            all_objects.extend(User.objects.filter(institution_id=inst_id))

        # Descubrimiento de modelos TenantModel
        # Ordenamos por dependencias (simplificado: core primero, luego el resto)
        models_to_process = []
        for model in apps.get_models():
            if model in [Institution, User]: continue
            if issubclass(model, TenantModel):
                models_to_process.append(model)
        
        # Nota: En un sistema complejo aquí usaríamos serializers.sort_dependencies
        # pero para TenantModel, el filtrado es la prioridad.
        for model in models_to_process:
            opts = model._meta
            qs = model._base_manager.filter(institution_id=inst_id)
            count = qs.count()
            if count > 0:
                self.stdout.write(f"  - [{opts.label}] -> {count} registros")
                all_objects.extend(list(qs))

        # 2. Serialización y Salida
        if fmt == 'json':
            self.export_json(all_objects, output_path)
        else:
            self.export_sql(all_objects, output_path)

        self.stdout.write(self.style.SUCCESS(f"\n✅ Backup finalizado: {output_path}"))

    def export_json(self, objects, path):
        self.stdout.write(f"Serializando {len(objects)} objetos a JSON...")
        with open(path, 'w', encoding='utf-8') as f:
            serializers.serialize("json", objects, stream=f, indent=2, use_natural_foreign_keys=True)

    def export_sql(self, objects, path):
        self.stdout.write(f"Generando sentencias SQL para {len(objects)} objetos...")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"-- Eduka360 Tenant Dump | ID: {objects[0].id if objects else 'N/A'}\n")
            f.write(f"-- Fecha: {datetime.now()}\n")
            f.write("BEGIN;\n")
            f.write("SET CONSTRAINTS ALL DEFERRED;\n\n")
            
            for obj in objects:
                table = obj._meta.db_table
                fields = []
                values = []
                
                for field in obj._meta.fields:
                    fields.append(field.column)
                    val = getattr(obj, field.attname)
                    if val is None:
                        values.append("NULL")
                    elif isinstance(val, (int, float)):
                        values.append(str(val))
                    elif isinstance(val, bool):
                        values.append("TRUE" if val else "FALSE")
                    else:
                        # Escape simple para strings
                        escaped = str(val).replace("'", "''")
                        values.append(f"'{escaped}'")
                
                sql = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({', '.join(values)}) ON CONFLICT (id) DO UPDATE SET {', '.join([f'{f}=EXCLUDED.{f}' for f in fields])};\n"
                f.write(sql)
            
            f.write("\nCOMMIT;\n")
