"""
Management command: generate_system_snapshot
Genera un snapshot actualizado del estado del sistema ERP-EDUCATIVA.
Uso: python manage.py generate_system_snapshot [--output ARCHIVO]
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.urls import get_resolver
from datetime import datetime
import os


class Command(BaseCommand):
    help = 'Genera un snapshot del sistema: tablas, endpoints, modelos y migraciones.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            default='SYSTEM_SNAPSHOT.md',
            help='Archivo de salida (default: SYSTEM_SNAPSHOT.md en la raíz del proyecto)'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        lines = []

        # Encabezado
        lines.append(f"# System Snapshot — ERP-EDUCATIVA")
        lines.append(f"**Generado**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 1. Tablas de la base de datos
        lines.append("## Base de Datos")
        lines.append("")
        tables = connection.introspection.table_names()
        custom_tables = sorted([
            t for t in tables
            if not t.startswith('django_') and not t.startswith('auth_')
            and not t.startswith('celery') and t != 'spatial_ref_sys'
        ])
        modules = {}
        for t in custom_tables:
            prefix = t.split('_')[0]
            modules.setdefault(prefix, []).append(t)

        for module, tbls in sorted(modules.items()):
            lines.append(f"### `{module}`")
            for tbl in tbls:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
                        count = cursor.fetchone()[0]
                    lines.append(f"- `{tbl}` ({count} registros)")
                except Exception:
                    lines.append(f"- `{tbl}`")
            lines.append("")

        # 2. Endpoints API
        lines.append("## Endpoints API")
        lines.append("")
        try:
            def list_urls(urlpatterns, prefix=''):
                routes = []
                for pattern in urlpatterns:
                    if hasattr(pattern, 'url_patterns'):
                        routes.extend(list_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
                    else:
                        routes.append(prefix + str(pattern.pattern))
                return routes

            urls = list_urls(get_resolver().url_patterns)
            api_urls = sorted(set(
                u for u in urls
                if u.startswith('api/') and not '<format>' in u
            ))
            for url in api_urls:
                lines.append(f"- `/{url}`")
        except Exception as e:
            lines.append(f"Error al listar URLs: {e}")
        lines.append("")

        # 3. Estado de migraciones
        lines.append("## Estado de Migraciones")
        lines.append("")
        try:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if plan:
                lines.append("⚠️ **Hay migraciones pendientes:**")
                for migration, backwards in plan:
                    lines.append(f"- `{migration.app_label}.{migration.name}`")
            else:
                lines.append("✅ Todas las migraciones están aplicadas.")
        except Exception as e:
            lines.append(f"Error al verificar migraciones: {e}")
        lines.append("")

        # 4. Usuarios y roles
        lines.append("## Usuarios por Rol")
        lines.append("")
        try:
            from users.models import User
            from django.db.models import Count
            roles = User.objects.values('role').annotate(total=Count('id')).order_by('role')
            for r in roles:
                lines.append(f"- **{r['role']}**: {r['total']} usuarios")
        except Exception as e:
            lines.append(f"Error: {e}")
        lines.append("")

        # 5. Cursos LMS
        lines.append("## Estado LMS")
        lines.append("")
        try:
            from learning.models import LMSCourse, CourseGroup, CourseTag
            lines.append(f"- Grupos: {CourseGroup.objects.count()}")
            lines.append(f"- Etiquetas: {CourseTag.objects.count()}")
            lines.append(f"- Cursos LMS: {LMSCourse.objects.count()}")
            lines.append(f"- Cursos sin etiqueta: {LMSCourse.objects.filter(tag__isnull=True).count()}")
        except Exception as e:
            lines.append(f"Error: {e}")
        lines.append("")

        # Escribir archivo
        content = "\n".join(lines)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f'✅ Snapshot generado: {output_file}'))
        self.stdout.write(f'   Tablas documentadas: {len(custom_tables)}')
        self.stdout.write(f'   Endpoints documentados: {len(api_urls)}')
