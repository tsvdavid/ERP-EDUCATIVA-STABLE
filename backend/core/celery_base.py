import celery
from django.db import connection
from core.thread_context import set_current_tenant_id, get_current_tenant_id, clear_current_tenant

class TenantAwareTask(celery.Task):
    """
    Clase base para tareas de Celery que asegura la persistencia del context Multi-tenant.
    1. Captura el tenant_id actual del hilo que dispara la tarea.
    2. Lo pasa como argumento oculto o metadato.
    3. Al ejecutar en el worker, inyecta el ID en Postgres para RLS.
    """
    
    def apply_async(self, args=None, kwargs=None, **options):
        # Capturar el tenant actual si no se proporciona explícitamente
        if kwargs is None:
            kwargs = {}
        
        if 'tenant_id' not in kwargs:
            kwargs['tenant_id'] = get_current_tenant_id()
            
        return super().apply_async(args=args, kwargs=kwargs, **options)

    def __call__(self, *args, **kwargs):
        tenant_id = kwargs.pop('tenant_id', None)
        
        # Establecer contexto en el worker
        if tenant_id:
            set_current_tenant_id(tenant_id)
            with connection.cursor() as cursor:
                # Usamos SET (no LOCAL) porque el worker maneja su propia sesión
                cursor.execute(f"SET app.current_tenant = '{tenant_id}';")
        else:
            # Bloqueo fail-safe
            set_current_tenant_id(0)
            with connection.cursor() as cursor:
                cursor.execute("SET app.current_tenant = '0';")
        
        try:
            return super().__call__(*args, **kwargs)
        finally:
            # Limpiar al terminar la tarea
            with connection.cursor() as cursor:
                cursor.execute("RESET app.current_tenant;")
            clear_current_tenant()
