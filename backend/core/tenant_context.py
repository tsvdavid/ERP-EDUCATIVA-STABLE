from django.db import connection
from contextlib import contextmanager
from core.thread_context import set_current_tenant_id, clear_current_tenant

@contextmanager
def tenant_context(institution_id):
    """Cambia temporalmente el tenant de la sesión de DB para operaciones autorizadas.
    Fuerza el uso de la misma conexión para todas las operaciones dentro del bloque.
    """
    # Obtener la conexión actual y asegurar que está abierta
    conn = connection.connection
    if not conn:
        connection.ensure_connection()
        conn = connection.connection
    
    try:
        set_current_tenant_id(institution_id)
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.rls_mode = %s", ['tenant'])
            cursor.execute("SET LOCAL app.current_tenant = %s", [str(institution_id)])
        yield
    finally:
        clear_current_tenant()
        with connection.cursor() as cursor:
            cursor.execute("RESET app.current_tenant")
            cursor.execute("RESET app.rls_mode")
