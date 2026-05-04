from celery import shared_task
from django.core.mail import get_connection, EmailMessage
from django.template import Context, Template
from django.utils import timezone
from .models import EmailConfig, EmailTemplate, EmailLog
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_invoice_email_task(self, invoice_id, recipient=None, sent_by_id=None, send_type='AUTO', **kwargs):
    """
    Tarea robusta para enviar correos de facturas con reintentos y persistencia de estado.
    """
    from treasury.models import Invoice
    
    try:
        invoice = Invoice.objects.select_related('institution').get(id=invoice_id)
        
        # 1. Actualizar estado inicial en Invoice e intentos
        # Si es el primer intento (no es un retry de Celery), incrementamos contador
        if self.request.retries == 0:
            invoice.email_attempts_count += 1
            invoice.email_status = 'PENDING'
        else:
            invoice.email_status = 'RETRYING'
        invoice.save()

        # 2. Obtener destinatario y validación previa
        final_recipient = recipient or invoice.client_email
        if not final_recipient:
            invoice.email_status = 'FAILED'
            invoice.save()
            logger.error(f"Invoice {invoice.id} has no recipient email.")
            return False

        # 3. Preparar Contenido y Log
        config = EmailConfig.objects.filter(institution=invoice.institution, is_active=True).first()
        if not config:
            raise Exception(f"No active EmailConfig found for institution {invoice.institution.id}")

        template = EmailTemplate.objects.filter(institution=invoice.institution, code='invoice_sent', is_active=True).first()
        
        # Contexto para la plantilla
        ctx = {
            'invoice': invoice,
            'client_name': invoice.client_name,
            'institution': invoice.institution.name,
            'amount': invoice.total,
            'number': invoice.number,
            'issue_date': invoice.issue_date
        }

        if not template:
            subject = f"Factura {invoice.number} - {invoice.institution.name}"
            body = f"Estimado(a) {invoice.client_name}, adjunto encontrará su factura electrónica No. {invoice.number} por un valor de ${invoice.total}."
        else:
            # Renderizar subject y body usando Django Templates
            subject = Template(template.subject).render(Context(ctx))
            body = Template(template.html_body).render(Context(ctx))
            
        log = EmailLog.objects.create(
            institution=invoice.institution,
            recipient=final_recipient,
            subject=subject,
            body=body,
            status='queued',
            reference_id=str(invoice.id),
            module_origin='treasury.invoice',
            send_type=send_type,
            sent_by_id=sent_by_id
        )
        
        # Vincular log a la factura
        invoice.last_email_log = log
        invoice.save()

        # 4. Configurar conexión SMTP y enviar Correo
        connection = get_connection(
            host=config.smtp_host,
            port=config.smtp_port,
            username=config.smtp_user,
            password=config.get_password(),
            use_tls=config.use_tls,
            use_ssl=config.use_ssl,
            timeout=20
        )

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=f"{config.sender_name} <{config.sender_email}>",
            to=[final_recipient],
            connection=connection
        )
        email.content_subtype = "html"

        # Adjuntar PDF y XML
        from treasury.utils import generate_invoice_pdf
        pdf_content = generate_invoice_pdf(invoice)
        email.attach(f"Factura_{invoice.number}.pdf", pdf_content, 'application/pdf')

        if invoice.xml_content:
            email.attach(f"Factura_{invoice.number}.xml", invoice.xml_content.encode('utf-8'), 'application/xml')

        email.send()

        # 5. Éxito: Actualizar Log e Invoice
        log.status = 'sent'
        log.sent_at = timezone.now()
        log.save()

        invoice.email_status = 'SENT'
        invoice.last_email_sent_at = timezone.now()
        invoice.save()
        
        return True

    except Exception as exc:
        # Registro del error
        error_msg = str(exc)
        logger.warning(f"Error sending email for invoice {invoice_id}: {error_msg}. Retry {self.request.retries}/3")
        
        # Lógica de reintentos con Celery
        if self.request.retries < self.max_retries:
            # Delays: 1m, 5m, 15m
            retry_delays = [60, 300, 900]
            delay = retry_delays[self.request.retries] if self.request.retries < len(retry_delays) else 1800
            
            try:
                inv = Invoice.objects.get(id=invoice_id)
                inv.email_status = 'RETRYING'
                inv.save()
            except: pass
            
            raise self.retry(exc=exc, countdown=delay)
        else:
            # Se agotaron los intentos
            try:
                inv = Invoice.objects.get(id=invoice_id)
                inv.email_status = 'FAILED'
                inv.save()
                
                # Actualizar el último log si existe
                if inv.last_email_log:
                    inv.last_email_log.status = 'failed'
                    inv.last_email_log.error_message = f"Agotados reintentos: {error_msg}"
                    inv.last_email_log.save()
                else:
                    # Crear log de fallo si no se pudo ni siquiera crear el log inicial
                    EmailLog.objects.create(
                        institution=inv.institution,
                        recipient=recipient or inv.client_email or 'N/A',
                        subject="Error de envío",
                        body=error_msg,
                        status='failed',
                        error_message=error_msg,
                        reference_id=str(inv.id),
                        module_origin='treasury.invoice'
                    )
            except Exception as e:
                logger.error(f"Critical error updating invoice failure state: {str(e)}")
                
            return False
