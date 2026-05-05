import logging
from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Institution, User
from .serializers import InstitutionSerializer, UserSerializer, UserCreateSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .permissions import CanManageInstitution, CanManageUser, IsAdminUser, IsLocalAdminUser, IsAcademicStaff, IsTreasuryStaff
from .tenant_mixins import InstitutionFilterMixin

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['role'] = user.role
        token['username'] = user.username
        token['institution'] = user.institution.id if user.institution else None
        token['wizard_completed'] = user.institution.wizard_completed if user.institution else True
        return token

    def validate(self, attrs):
        print(f"DEBUG: Validating login for user: {attrs.get('username')}")
        try:
            data = super().validate(attrs)
            print(f"DEBUG: Validation success for user: {attrs.get('username')}")
            return data
        except Exception as e:
            print(f"DEBUG: Validation failed for user: {attrs.get('username')}. Error: {str(e)}")
            raise e

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

from rest_framework.views import APIView

class SwitchInstitutionView(APIView):
    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.response import Response
        
        refresh_token = request.data.get('refresh_token')
        new_institution_id = request.data.get('institution_id')
        
        if not refresh_token or not new_institution_id:
            return Response({'error': 'refresh_token e institution_id requeridos'}, status=400)
        
        refresh = RefreshToken(refresh_token)
        user_id = refresh.payload.get('user_id')
        
        from users.models import User
        user_obj = User.objects.get(id=user_id)
        
        if not user_obj.is_superuser and user_obj.institution_id != new_institution_id:
            return Response({'error': 'No autorizado'}, status=403)
        
        new_refresh = RefreshToken.for_user(user_obj)
        new_refresh['institution'] = new_institution_id
        new_refresh['role'] = user_obj.role
        
        return Response({
            'access': str(new_refresh.access_token),
            'refresh': str(new_refresh),
            'institution_id': new_institution_id
        })

class InstitutionViewSet(viewsets.ModelViewSet):
    """
    Gestión de Instituciones.
    Admin Global: CRUD completo sobre todas.
    Rector: Solo Lectura/Actualización de la propia.
    """
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageInstitution]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return Institution.objects.all().order_by('name')
        
        # Rectores solo ven su propia institución
        if hasattr(user, 'institution') and user.institution:
            return Institution.objects.filter(id=user.institution.id)
            
        return Institution.objects.none()

    @action(detail=False, methods=['get'], url_path='required-fields')
    def required_fields(self, request):
        return Response({
            "required_fields": ['name', 'ruc', 'address', 'phone', 'email', 'establishment_code', 'emission_point'],
            "message": "Estos campos son obligatorios para crear una institución y ejecutar el proceso de bootstrap."
        })

    @action(detail=True, methods=['get'], url_path='health-check')
    def health_check(self, request, pk=None):
        """
        Alias for setup-status with extra health checks.
        """
        institution = self.get_object()
        
        # Check components
        from accounting.models import Account, AccountingConfig, FiscalYear
        from treasury.models import PaymentMethod
        
        status_data = {
            'institution_id': institution.id,
            'setup_status': institution.setup_status,
            'wizard_completed': institution.wizard_completed,
            'components': {
                'chart_accounts': Account.objects.filter(institution=institution).count(),
                'accounting_configs': AccountingConfig.objects.filter(institution=institution).count(),
                'fiscal_year_active': FiscalYear.objects.filter(institution=institution, is_closed=False).exists(),
                'payment_methods': PaymentMethod.objects.filter(institution=institution).count(),
            },
            'sri_config': {
                'has_ruc': bool(institution.ruc),
                'has_signature': bool(institution.electronic_signature),
                'has_establishment': bool(institution.establishment_code),
            }
        }
        
        return Response(status_data)

    @action(detail=True, methods=['post'], url_path='retry-bootstrap')
    def retry_bootstrap(self, request, pk=None):
        institution = self.get_object()
        from .services import InstitutionBootstrapService
        try:
            InstitutionBootstrapService.bootstrap(institution)
            return Response({'status': 'Bootstrap re-executed successfully', 'new_status': institution.setup_status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='setup-status')
    def setup_status(self, request, pk=None):
        # Keep old action for compatibility or redirect to health-check
        return self.health_check(request, pk)

    def perform_create(self, serializer):
        # Permitir creación solo a Admin Global o Superuser
        if not (self.request.user.role == 'ADMIN' or self.request.user.is_superuser):
            raise PermissionDenied("Solo el Administrador Global puede crear instituciones.")
        
        # Validación extra de seguridad (aunque ya esté en el serializer)
        required_fields = ['name', 'ruc', 'address', 'phone', 'email', 'establishment_code', 'emission_point']
        for field in required_fields:
            if not serializer.validated_data.get(field):
                raise ValidationError({"error": f"Falta campo requerido: {field}"})

        logger = logging.getLogger(__name__)
        from .services import InstitutionBootstrapService
        
        try:
            with transaction.atomic():
                logger.info(f"Iniciando bootstrap para nueva institución: {serializer.validated_data.get('name')}")
                InstitutionBootstrapService.create_and_bootstrap(serializer.validated_data)
                logger.info("Bootstrap completado exitosamente.")
        except Exception as e:
            logger.error(f"Fallo en bootstrap de institución: {str(e)}", exc_info=True)
            raise ValidationError({"error": f"Error during institution bootstrap: {str(e)}"})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Protección de integridad: No borrar si hay usuarios o registros académicos vinculados
        if instance.users.exists():
            return Response(
                {"error": "No se puede eliminar una institución con usuarios registrados."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Podríamos añadir más checks aquí (ej: instance.academic_years.exists())
        if hasattr(instance, 'academic_years') and instance.academic_years.exists():
            return Response(
                {"error": "No se puede eliminar una institución con años lectivos configurados."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='hard-delete')
    def hard_delete(self, request, pk=None):
        """
        Borrado Forzado para Superusuarios. 
        Limpia en cascada todos los datos vinculados.
        """
        if not request.user.is_superuser:
            raise PermissionDenied("Solo los superusuarios pueden realizar borrados forzados.")
            
        instance = self.get_object()
        logger = logging.getLogger(__name__)
        
        try:
            with transaction.atomic():
                logger.warning(f"Iniciando borrado forzado de institución: {instance.name} (ID: {instance.id})")
                
                # 1. Borrar datos de suscripción
                from subscriptions.models import Subscription, SubscriptionPayment, SubscriptionAuditLog, SubscriptionModule
                SubscriptionPayment.objects.filter(subscription__institution=instance).delete()
                SubscriptionModule.objects.filter(subscription__institution=instance).delete()
                Subscription.objects.filter(institution=instance).delete()
                SubscriptionAuditLog.objects.filter(institution=instance).delete()
                
                # 2. Borrar datos académicos
                from academic.models import AcademicYear, Course, Subject, Enrollment, Attendance, Grade
                Attendance.objects.filter(enrollment__course__academic_year__institution=instance).delete()
                Grade.objects.filter(enrollment__course__academic_year__institution=instance).delete()
                Enrollment.objects.filter(course__academic_year__institution=instance).delete()
                Subject.objects.filter(institution=instance).delete()
                Course.objects.filter(academic_year__institution=instance).delete()
                AcademicYear.objects.filter(institution=instance).delete()

                # 3. Borrar contabilidad y tesorería
                from accounting.models import Account, AccountingConfig, FiscalYear, Entry, EntryLine
                EntryLine.objects.filter(entry__institution=instance).delete()
                Entry.objects.filter(institution=instance).delete()
                FiscalYear.objects.filter(institution=instance).delete()
                AccountingConfig.objects.filter(institution=instance).delete()
                Account.objects.filter(institution=instance).delete()
                
                from treasury.models import PaymentMethod, Concept, Customer, Invoice, Payment, CashBox
                Payment.objects.filter(invoice__institution=instance).delete()
                Invoice.objects.filter(institution=instance).delete()
                CashBox.objects.filter(institution=instance).delete()
                PaymentMethod.objects.filter(institution=instance).delete()
                Concept.objects.filter(institution=instance).delete()
                Customer.objects.filter(institution=instance).delete()

                # 4. Borrar Usuarios
                User.objects.filter(institution=instance).delete()

                # 5. Borrar Institución (Hard delete)
                # Usamos el delete() de la superclase para evitar el soft delete override
                super(Institution, instance).delete()
                
                logger.info(f"Institución {instance.id} borrada exitosamente de forma permanente.")
                return Response({'message': 'Institución y todos sus datos han sido eliminados permanentemente.'})
                
        except Exception as e:
            logger.error(f"Error en borrado forzado: {str(e)}", exc_info=True)
            return Response({'error': f"Error durante el borrado forzado: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('institution').prefetch_related('children')
    serializer_class = UserSerializer
    tenant_field = 'institution'
    
    def get_permissions(self):
        from .permissions import CanManageUser
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), CanManageUser()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # HARDENING: Inyectar institución del creador si no es superuser
        inst = self.request.user.institution
        serializer.save(institution=inst)

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            role = self.request.query_params.get('role', None)
            if role:
                queryset = queryset.filter(role=role)
                # Restriction for Teachers viewing Students
                if role == 'STUDENT' and self.request.user.role == 'TEACHER':
                    queryset = queryset.filter(enrollments__course__subjects__teacher=self.request.user).distinct()
            
            return queryset
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
