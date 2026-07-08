from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import EmailConfig, EmailTemplate, EmailLog
from .serializers import EmailConfigSerializer, EmailTemplateSerializer, EmailLogSerializer
from core.tenancy.viewsets import BaseTenantViewSet
from users.tenant_mixins import InstitutionFilterMixin
from users.permissions import IsAdminUser, IsLocalAdminUser, IsTreasuryStaff, IsAccountantUser
from django.core.mail import get_connection
import logging

logger = logging.getLogger(__name__)

class EmailConfigViewSet(BaseTenantViewSet, InstitutionFilterMixin):
    """Gestión de configuración SMTP de la institución."""
    queryset = EmailConfig.objects.all()
    serializer_class = EmailConfigSerializer
    permission_classes = [permissions.IsAuthenticated, IsLocalAdminUser | IsAccountantUser]

    def get_queryset(self):
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        # HARDENING: Forzar evaluación explícita (Opción B del requerimiento anterior)
        # Esto garantiza que el queryset se ejecute con el contexto de RLS actual
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        # Simple create – tenant injected by BaseTenantViewSet
        serializer.save()

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Prueba la conexión SMTP actual usando smtplib directamente para mayor control de timeouts."""
        config = self.get_object()
        logger.info(
            f"Iniciando prueba SMTP (Institución: {config.institution_id}, Host: {config.smtp_host}:{config.smtp_port})"
        )

        import smtplib
        import socket

        try:
            if config.use_ssl:
                smtp = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=5)
            else:
                smtp = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=5)
            if config.use_tls and not config.use_ssl:
                smtp.starttls(timeout=5)
            smtp.login(config.smtp_user, config.get_password())
            smtp.quit()
            return Response(
                {'status': 'success', 'message': '¡Conexión exitosa!'},
                status=status.HTTP_200_OK,
            )
        except (socket.timeout, TimeoutError):
            return Response(
                {'status': 'error', 'message': 'Timeout al conectar con el servidor SMTP.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except smtplib.SMTPAuthenticationError:
            return Response(
                {'status': 'error', 'message': 'Error de autenticación SMTP.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error inesperado en prueba SMTP: {str(e)}")
            return Response(
                {'status': 'error', 'message': f"Error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
class EmailTemplateViewSet(BaseTenantViewSet, InstitutionFilterMixin):
    """Gestión de plantillas de correo."""
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsLocalAdminUser | IsAccountantUser]

    def perform_create(self, serializer):
        # Tenant injected automatically by BaseTenantViewSet
        serializer.save()

class EmailLogViewSet(BaseTenantViewSet, InstitutionFilterMixin, viewsets.ReadOnlyModelViewSet):
    """Lectura de logs de envío."""
    queryset = EmailLog.objects.all()
    serializer_class = EmailLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsLocalAdminUser | IsTreasuryStaff | IsAccountantUser]

    def get_queryset(self):
        qs = super().get_queryset()
        module = self.request.query_params.get('module')
        if module:
            qs = qs.filter(module_origin=module)
        return qs
