import threading

_thread_locals = threading.local()

def set_current_tenant_id(tenant_id):
    """Establece el ID del tenant para el hilo actual."""
    setattr(_thread_locals, 'tenant_id', tenant_id)

def get_current_tenant_id():
    """Retorna el ID del tenant del hilo actual."""
    return getattr(_thread_locals, 'tenant_id', None)

def clear_current_tenant():
    """Limpia el contexto del hilo."""
    if hasattr(_thread_locals, 'tenant_id'):
        delattr(_thread_locals, 'tenant_id')
