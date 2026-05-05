from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import Institution
from .models import EmailConfig, EmailTemplate

@receiver(post_save, sender=Institution)
def create_default_email_settings(sender, instance, created, **kwargs):
    """Crea configuración SMTP base y plantillas esenciales para nuevas instituciones."""
    if created:
        from core.tenant_context import tenant_context
        with tenant_context(instance.id):
                # 1. Crear EmailConfig vacío (Estado inicial para que la UI lo detecte)
            EmailConfig.objects.get_or_create(
                institution=instance,
                defaults={
                    'smtp_host': 'smtp.example.com',
                    'smtp_port': 587,
                    'is_active': False,
                    'sender_name': instance.name,
                    'sender_email': instance.email or 'noreply@eduka360.com'
                }
            )
        
            # 2. Crear Plantillas Base
            templates = [
                {
                    'code': 'invoice_sent',
                    'subject': '📚 Comprobante Electrónico - {{ institution_name }}',
                    'html_body': """
                    <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
                        <div style="text-align: center; margin-bottom: 20px;">
                            <h2 style="color: #2c3e50; margin: 0;">{{ institution_name }}</h2>
                            <p style="color: #7f8c8d; font-size: 14px;">Comprobantes Electrónicos</p>
                        </div>
                    
                        <h3 style="color: #2c3e50;">¡Hola {{ customer_name }}!</h3>
                        <p>Informamos que se ha generado un nuevo comprobante electrónico a tu nombre con los siguientes detalles:</p>
                    
                        <div style="background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin: 25px 0;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px 0; color: #64748b; font-weight: bold;">Documento:</td>
                                    <td style="padding: 8px 0; color: #1e293b; text-align: right;">Factura</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #64748b; font-weight: bold;">Número:</td>
                                    <td style="padding: 8px 0; color: #1e293b; text-align: right;">{{ document_number }}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #64748b; font-weight: bold;">Fecha:</td>
                                    <td style="padding: 8px 0; color: #1e293b; text-align: right;">{{ issue_date }}</td>
                                </tr>
                                <tr style="border-top: 1px solid #e2e8f0;">
                                    <td style="padding: 12px 0 0 0; color: #64748b; font-weight: bold; font-size: 18px;">Total:</td>
                                    <td style="padding: 12px 0 0 0; color: #3b82f6; font-weight: bold; font-size: 18px; text-align: right;">${{ total_amount }}</td>
                                </tr>
                            </table>
                        </div>
                    
                        <p>Encontrarás los archivos PDF y XML adjuntos a este mensaje de correo.</p>
                        <p>Gracias por tu atención.</p>
                    
                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #94a3b8; font-size: 12px;">
                            <p>© {{ institution_name }} | Eduka360 - Gestión Educativa Inteligente</p>
                        </div>
                    </div>
                    """
                },
                {
                    'code': 'welcome',
                    'subject': 'Bienvenido a {{ institution_name }}',
                    'html_body': "<p>Hola {{ user_name }}, bienvenido a nuestra plataforma.</p>"
                }
            ]
        
            for t in templates:
                EmailTemplate.objects.get_or_create(
                    institution=instance,
                    code=t['code'],
                    defaults={
                        'subject': t['subject'],
                        'html_body': t['html_body'],
                        'is_active': True
                    }
                )
