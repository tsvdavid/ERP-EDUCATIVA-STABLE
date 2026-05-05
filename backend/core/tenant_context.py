from django.db import connection
from contextlib import contextmanager

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
        with connection.cursor() as cursor:
            cursor.execute(f"SET LOCAL app.current_tenant = {institution_id}")
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET app.current_tenant")
