from django.template import Context, Template
from .models import EmailTemplate, EmailLog, EmailConfig
from .tasks import send_async_email
import logging

logger = logging.getLogger(__name__)

def send_tenant_email(institution, template_code, recipient, context_data, reference_id="", module_origin="", attachments=None):
    """
    Función principal para enviar correos transaccionales multi-tenant.
    Busca la plantilla, renderiza el contenido y encola la tarea de envío.
    """
    try:
        # 1. Buscar plantilla
        template = EmailTemplate.objects.filter(institution=institution, code=template_code, is_active=True).first()
        if not template:
            logger.error(f"Template {template_code} not found for institution {institution.id}")
            return None
            
        # 2. Renderizar contenido
        django_template = Template(template.html_body)
        django_subject = Template(template.subject)
        
        context = Context(context_data)
        rendered_body = django_template.render(context)
        rendered_subject = django_subject.render(context)
        
        # 3. Crear Log (en estado 'queued')
        log = EmailLog.objects.create(
            institution=institution,
            recipient=recipient,
            subject=rendered_subject,
            body=rendered_body,
            status='queued',
            reference_id=str(reference_id),
            module_origin=module_origin
        )
        
        # 4. Encolar tarea de Celery
        # Nota: Los adjuntos se manejarán en una versión extendida de la tarea
        # que reciba rutas de archivos temporales o similares.
        send_async_email.delay(log.id)
        
        return log
        
    except Exception as e:
        logger.exception("Error initiating tenant email")
        return None
