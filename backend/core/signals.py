from django.db.models.signals import post_save, post_delete
ocean_signals = True # Flag to avoid recursion if needed
from django.dispatch import receiver
from django.db import models
from .models import ActionLog
import json

def get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(post_save)
def audit_log_save(sender, instance, created, **kwargs):
    # Evitar loguear el propio ActionLog para no entrar en bucle
    if sender == ActionLog:
        return

    # Solo loguear modelos críticos o que hereden de TenantModel
    from users.models import Institution, User
    from accounting.models import MonthlyClose, FiscalYear, JournalEntry
    
    critical_models = [Institution, User, MonthlyClose, FiscalYear, JournalEntry]
    if sender not in critical_models:
        return

    action = 'CREATE' if created else 'UPDATE'
    
    # Intentar obtener el usuario de la request actual
    # Nota: Esto requiere que guardemos el usuario en un threadlocal o similar.
    # Como no hemos implementado CUM o similar, por ahora el log será parcial
    # Pero el trigger está listo.
    
    # En un sistema maduro, usaríamos un middleware que guarde el usuario en threadlocal
    # Por ahora registramos la acción a nivel de base de datos.
    
    ActionLog.objects.create(
        action=action,
        model_name=sender.__name__,
        object_id=str(instance.pk),
        institution=getattr(instance, 'institution', None) if sender == User else (instance if sender == Institution else None),
        description=f"{action} en {sender.__name__} ID {instance.pk}"
    )

@receiver(post_delete)
def audit_log_delete(sender, instance, **kwargs):
    if sender == ActionLog:
        return

    from users.models import Institution, User
    from accounting.models import MonthlyClose, FiscalYear, JournalEntry
    
    critical_models = [Institution, User, MonthlyClose, FiscalYear, JournalEntry]
    if sender not in critical_models:
        return

    ActionLog.objects.create(
        action='DELETE',
        model_name=sender.__name__,
        object_id=str(instance.pk),
        institution=getattr(instance, 'institution', None) if sender == User else (instance if sender == Institution else None),
        description=f"Eliminación de {sender.__name__} ID {instance.pk}"
    )
