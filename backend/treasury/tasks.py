import logging
from celery import shared_task
from django.utils import timezone
from .models import Invoice
from .sri.client import SriClient
from .sri.signer import XadesSigner
from .sri.xml_generator import InvoiceXmlBuilder
import os

logger = logging.getLogger(__name__)
from django.conf import settings

@shared_task(bind=True, max_retries=10)
def process_invoice_sri(self, invoice_id, tenant_id: int, **kwargs):
    if not tenant_id:
        raise ValueError("tenant_id required")
    """
    Task principal para procesar una factura ante el SRI.
    1. Generar/Firmar si no está firmado.
    2. Enviar a Recepción.
    3. Si falla con 500, reintentar con backoff.
    """
    try:
        invoice = Invoice.objects.get(id=invoice_id, institution_id=tenant_id)
    except Invoice.DoesNotExist:
        return f"Invoice {invoice_id} not found"

    # 1. Asegurar XML firmado
    if not invoice.xml_content:
        try:
            builder = InvoiceXmlBuilder(invoice)
            access_key, xml_content = builder.build_xml()
            invoice.access_key = access_key
            
            inst = invoice.institution
            if not inst.electronic_signature:
                invoice.sri_status = 'REJECTED'
                invoice.sri_response = {'error': 'No hay firma configurada'}
                invoice.save()
                return "No signature"
                
            signer = XadesSigner(inst.electronic_signature.path, inst.signature_password)
            with open("TRACE_1_XML_ORIGINAL.xml", "wb") as f:
                f.write(xml_content.encode("utf-8"))
            signed_xml = signer.sign_xml(xml_content)
            
            invoice.xml_content = signed_xml
            invoice.sri_status = 'SIGNED'
            invoice.save()
        except Exception as e:
            logger.error(f"Error firmando factura {invoice_id}: {e}")
            invoice.sri_status = 'REJECTED'
            invoice.sri_response = {'error': str(e)}
            invoice.save()
            return f"Sign error: {e}"

    # 2. Enviar a Recepción
    inst = invoice.institution
    urls = {
        'reception_test': inst.sri_url_reception_test,
        'authorization_test': inst.sri_url_authorization_test,
        'reception_prod': inst.sri_url_reception_prod,
        'authorization_prod': inst.sri_url_authorization_prod
    }
    client = SriClient(inst.sri_environment, urls=urls)
    success, msg, status_code, messages = client.send_receipt(invoice.xml_content)
    
    invoice.sri_attempts += 1
    invoice.sri_response = invoice.sri_response or {}
    invoice.sri_response['reception'] = {
        'msg': msg, 
        'status': status_code, 
        'messages': messages,
        'at': str(timezone.now())
    }
    
    if success or status_code == 'RECIBIDA':
        invoice.sri_status = 'RECEIVED'
        invoice.save()
        # Encolar autorización
        poll_invoice_authorization.apply_async((invoice_id, tenant_id), countdown=15)
        return f"Comprobante Recibido: {msg}"
    else:
        # LOG XML for debugging SRI 35/39 errors
        try:
            log_dir = os.path.join(settings.MEDIA_ROOT, 'sri_logs', str(inst.id))
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, f"{invoice.number.replace('-', '_')}_rejected.xml")
            with open(log_path, 'w') as f:
                f.write(invoice.xml_content or "")
            logger.error(f"SRI REJECTION for {invoice.number}: XML logged to {log_path}")
        except Exception as log_err:
            logger.error(f"Could not log rejected XML: {log_err}")

        invoice.sri_status = 'REJECTED'
        invoice.save()
    
    # Manejo de error 500 intermitente (PersistenceException)
    if '500' in msg or 'PersistenceException' in msg:
        invoice.sri_status = 'PENDING_SRI'
        invoice.save()
        
        # Backoff exponencial: 5m, 15m, 30m, 1h, etc.
        retry_delays = [300, 900, 1800, 3600, 7200, 14400]
        delay = retry_delays[min(self.request.retries, len(retry_delays)-1)]
        
        logger.warning(f"SRI 500 for invoice {invoice_id}. Retrying in {delay}s. Attempt {self.request.retries}")
        raise self.retry(exc=Exception(f"SRI 500 error: {msg}"), countdown=delay)
    
    # Error fatal o devuelta
    invoice.sri_status = 'REJECTED'
    invoice.save()
    return f"Reception failed: {msg}"

@shared_task(bind=True, max_retries=20)
def poll_invoice_authorization(self, invoice_id, tenant_id: int, **kwargs):
    if not tenant_id:
        raise ValueError("tenant_id required")
    """
    Consulta el estado de autorización de la factura.
    """
    try:
        invoice = Invoice.objects.get(id=invoice_id, institution_id=tenant_id)
    except Invoice.DoesNotExist:
        return
        
    if not invoice.access_key:
        return "No access key"

    inst = invoice.institution
    urls = {
        'reception_test': inst.sri_url_reception_test,
        'authorization_test': inst.sri_url_authorization_test,
        'reception_prod': inst.sri_url_reception_prod,
        'authorization_prod': inst.sri_url_authorization_prod
    }
    client = SriClient(inst.sri_environment, urls=urls)
    success, msg, status, messages = client.request_authorization(invoice.access_key)
    
    invoice.sri_response = invoice.sri_response or {}
    invoice.sri_response['authorization'] = {
        'msg': msg, 
        'status': status, 
        'messages': messages,
        'at': str(timezone.now())
    }
    
    if success:
        invoice.sri_status = 'AUTHORIZED'
        invoice.sri_authorization_date = timezone.now()
        invoice.save()
        
        # Enviar email automáticamente al autorizar
        try:
            from notifications.tasks import send_invoice_email_task
            send_invoice_email_task.delay(invoice.id, tenant_id)
        except Exception as e:
            logger.error(f"Error enqueuing email after auth: {e}")
            
        return "Authorized"
        
    if status == 'PENDING' or 'EN PROCESO' in msg:
        # Sigue en proceso, reintentar en 60 segundos
        raise self.retry(countdown=60)
        
    if 'OFFLINE' in status or '500' in msg:
        # Error de conexión o SRI caído, reintentar en 5 minutos
        raise self.retry(countdown=300)

    # Rechazo formal (NO AUTORIZADO)
    invoice.sri_status = 'REJECTED'
    invoice.save()
    return f"Auth status: {status} - {msg}"
