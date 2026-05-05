from django.db import connection, transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import EmailConfig, EmailTemplate, EmailLog
from .serializers import EmailConfigSerializer, EmailTemplateSerializer, EmailLogSerializer
from users.tenant_mixins import InstitutionFilterMixin
from users.permissions import IsAdminUser, IsLocalAdminUser, IsTreasuryStaff, IsAccountantUser
from django.core.mail import get_connection
import logging

logger = logging.getLogger(__name__)

class EmailConfigViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    """Gestión de configuración SMTP de la institución."""
    queryset = EmailConfig.objects.all()
    serializer_class = EmailConfigSerializer
    permission_classes = [permissions.IsAuthenticated, IsLocalAdminUser | IsAccountantUser]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            with connection.cursor() as cursor:
                cursor.execute(f"SET app.current_tenant = '{tenant.id}';")
        else:
            # Fallback para superusuarios sin institución directa
            inst_id = self.request.headers.get('X-Institution-ID')
            if inst_id:
                with connection.cursor() as cursor:
                    cursor.execute(f"SET app.current_tenant = '{inst_id}';")
        
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        # HARDENING: Forzar evaluación explícita (Opción B del requerimiento anterior)
        # Esto garantiza que el queryset se ejecute con el contexto de RLS actual
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        # CIERRE FINAL: Upsert atómico con select_for_update para evitar condiciones de carrera
        from rest_framework.exceptions import ValidationError
        import logging
        logger = logging.getLogger(__name__)

        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
             # Fallback para superusuarios
             inst_id = self.request.headers.get('X-Institution-ID')
             if inst_id:
                 from users.models import Institution
                 tenant = Institution.objects.filter(id=inst_id).first()

        if not tenant:
             logger.error(f"Error en perform_create: No se detectó institución para el usuario {self.request.user}")
             raise ValidationError("Contexto de institución inválido.")

        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(f"SET LOCAL app.current_tenant = '{tenant.id}';")

                instance = EmailConfig.objects.select_for_update().filter(institution=tenant).first()
                if instance:
                    logger.info(f"Actualizando configuración existente para institución {tenant.id}")
                    serializer.instance = instance
                
                serializer.save(institution=tenant)
        except Exception as e:
            logger.exception(f"Error crítico guardando EmailConfig: {str(e)}")
            raise ValidationError(f"Error al guardar configuración: {str(e)}")

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Prueba la conexión SMTP actual usando smtplib directamente para mayor control de timeouts."""
        config = self.get_object()
        logger.info(f"Iniciando prueba SMTP (Institución: {config.institution_id}, Host: {config.smtp_host}:{config.smtp_port})")
        
        import smtplib
        import socket

        try:
            # Determinamos si usamos SSL (465) o TLS (587/25)
            if config.use_ssl:
                logger.info("Usando SMTP_SSL...")
                smtp = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=5)
            else:
                logger.info("Usando SMTP standard...")
                smtp = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=5)
            
            if config.use_tls and not config.use_ssl:
                logger.info("Iniciando STARTTLS...")
                smtp.starttls(timeout=5)
            
            logger.info("Intentando login...")
            smtp.login(config.smtp_user, config.get_password())
            
            logger.info("Login exitoso. Cerrando conexión.")
            smtp.quit()
            
            return Response({
                'status': 'success', 
                'message': '¡Conexión exitosa! El servidor SMTP aceptó las credenciales.'
            }, status=status.HTTP_200_OK)

        except (socket.timeout, TimeoutError):
            logger.error("Timeout al intentar conectar con el servidor SMTP")
            return Response({
                'status': 'error', 
                'message': 'Error de conexión: El servidor no respondió a tiempo (Timeout). Verifique el host y el puerto.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except smtplib.SMTPAuthenticationError:
            logger.error("Error de autenticación SMTP")
            return Response({
                'status': 'error', 
                'message': 'Error de autenticación: Usuario o contraseña incorrectos.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error inesperado en prueba SMTP: {str(e)}")
            return Response({
                'status': 'error', 
                'message': f"Error de conexión: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

class EmailTemplateViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    """Gestión de plantillas de correo."""
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsLocalAdminUser | IsAccountantUser]

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            inst_id = self.request.user.institution_id or self.request.headers.get('X-Institution-ID')
            if inst_id:
                from users.models import Institution
                tenant = Institution.objects.filter(id=inst_id).first()
                
        if not tenant:
             raise ValidationError("Se requiere un contexto de institución válido.")
             
        serializer.save(institution=tenant)

class EmailLogViewSet(InstitutionFilterMixin, viewsets.ReadOnlyModelViewSet):
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
