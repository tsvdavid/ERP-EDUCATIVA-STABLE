from django.core.management.base import BaseCommand
from notifications.models import EmailTemplate
from users.models import Institution
from django.utils.translation import gettext_lazy as _

class Command(BaseCommand):
    help = 'Seeds mandatory email templates for all institutions'

    def handle(self, *args, **options):
        institutions = Institution.objects.all()
        templates_count = 0

        for inst in institutions:
            # Factura Enviada
            template, created = EmailTemplate.objects.get_or_create(
                institution=inst,
                code='invoice_sent',
                defaults={
                    'subject': 'Factura Electrónica {{ invoice.number }} - {{ institution.name }}',
                    'html_body': """
                    <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px;">
                        <h2 style="color: #e11d48;">Comprobante Electrónico</h2>
                        <p>Estimado/a <strong>{{ customer.first_name }} {{ customer.last_name }}</strong>,</p>
                        <p>Le informamos que se ha generado un nuevo comprobante electrónico de la institución <strong>{{ institution.name }}</strong>.</p>
                        
                        <div style="background: #f9fafb; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <p style="margin: 5px 0;"><strong>Tipo:</strong> Factura</p>
                            <p style="margin: 5px 0;"><strong>Número:</strong> {{ invoice.number }}</p>
                            <p style="margin: 5px 0;"><strong>Total:</strong> ${{ invoice.total }}</p>
                            <p style="margin: 5px 0;"><strong>Fecha de Emisión:</strong> {{ invoice.issue_date }}</p>
                        </div>
                        
                        <p>Se adjuntan a este correo los archivos <strong>XML</strong> y <strong>PDF (RIDE)</strong> correspondientes.</p>
                        
                        <p style="color: #666; font-size: 12px; margin-top: 30px;">
                            Este es un correo automático, por favor no responda a este mensaje.
                        </p>
                    </div>
                    """,
                    'is_active': True
                }
            )
            if created:
                templates_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created template for {inst.name}'))

        self.stdout.write(self.style.SUCCESS(f'Finished seeding {templates_count} templates.'))
