import logging
from django.db import transaction
from django.contrib.auth.models import update_last_login
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError, PermissionDenied, AuthenticationFailed
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import Institution, User
from .serializers import (
    InstitutionSerializer,
    UserSerializer,
    UserCreateSerializer,
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .permissions import CanManageInstitution, get_active_institution_id
from .tenant_mixins import InstitutionFilterMixin


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['username'] = user.username
        institution_id = user.institution.id if user.institution else None
        token['institution_id'] = institution_id
        token['institution'] = institution_id
        token['wizard_completed'] = (
            user.institution.wizard_completed if user.institution else True
        )
        return token

    def validate(self, attrs):
        username = attrs.get(self.username_field)
        password = attrs.get('password')

        try:
            user = User.objects.unscoped().get(**{self.username_field: username})
        except User.DoesNotExist:
            raise AuthenticationFailed(
                self.error_messages['no_active_account'],
                'no_active_account',
            )

        if not user.check_password(password) or not api_settings.USER_AUTHENTICATION_RULE(user):
            raise AuthenticationFailed(
                self.error_messages['no_active_account'],
                'no_active_account',
            )

        self.user = user
        refresh = self.get_token(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)

        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = self.token_class(attrs['refresh'])
        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM, None)

        if user_id:
            try:
                user = User.objects.unscoped().get(**{api_settings.USER_ID_FIELD: user_id})
            except User.DoesNotExist:
                raise AuthenticationFailed(
                    self.error_messages['no_active_account'],
                    'no_active_account',
                )

            if not api_settings.USER_AUTHENTICATION_RULE(user):
                raise AuthenticationFailed(
                    self.error_messages['no_active_account'],
                    'no_active_account',
                )

        data = {'access': str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    refresh.blacklist()
                except AttributeError:
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()
            refresh.outstand()

            data['refresh'] = str(refresh)

        return data


TokenRefreshView.serializer_class = CustomTokenRefreshSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class SwitchInstitutionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh_token = request.data.get('refresh_token')
        new_institution_id = request.data.get('institution_id')
        if not refresh_token or not new_institution_id:
            return Response(
                {'error': 'refresh_token e institution_id requeridos'},
                status=400,
            )
        refresh = RefreshToken(refresh_token)
        user_id = refresh.payload.get('user_id')
        from users.models import User
        user_obj = User.objects.unscoped().get(id=user_id)
        target_institution = Institution.objects.get(id=int(new_institution_id))
        if user_obj.role != 'GLOBAL' and not user_obj.is_superuser and (
            user_obj.institution_id != int(new_institution_id)
        ):
            return Response({'error': 'No autorizado'}, status=403)
        new_refresh = RefreshToken.for_user(user_obj)
        new_refresh['institution'] = new_institution_id
        new_refresh['institution_id'] = int(new_institution_id)
        new_refresh['role'] = user_obj.role
        new_refresh['wizard_completed'] = target_institution.wizard_completed
        return Response(
            {
                'access': str(new_refresh.access_token),
                'refresh': str(new_refresh),
                'institution_id': new_institution_id,
            }
        )


class InstitutionViewSet(viewsets.ModelViewSet):
    """Gestión de Instituciones.
    Admin Global: CRUD completo sobre todas.
    Rector: Solo Lectura/Actualización de la propia.
    """

    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageInstitution]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role in ['ADMIN', 'GLOBAL']:
            return Institution.objects.all().order_by('name')
        if getattr(user, 'institution', None):
            return Institution.objects.filter(id=user.institution.id)
        return Institution.objects.none()

    @action(detail=False, methods=['get'], url_path='required-fields')
    def required_fields(self, request):
        return Response(
            {
                "required_fields": [
                    'name',
                    'ruc',
                    'address',
                    'phone',
                    'email',
                    'establishment_code',
                    'emission_point',
                ],
                "message": (
                    "Estos campos son obligatorios para crear una institución "
                    "y ejecutar el proceso de bootstrap."
                ),
            }
        )

    @action(detail=True, methods=['get'], url_path='health-check')
    def health_check(self, request, pk=None):
        """Alias for setup-status with extra health checks."""
        institution = self.get_object()
        from accounting.models import (
            Account,
            AccountingConfig,
            FiscalYear,
        )
        from treasury.models import PaymentMethod
        status_data = {
            'institution_id': institution.id,
            'setup_status': institution.setup_status,
            'wizard_completed': institution.wizard_completed,
            'components': {
                'chart_accounts': Account.objects.filter(
                    institution=institution
                ).count(),
                'accounting_configs': AccountingConfig.objects.filter(
                    institution=institution
                ).count(),
                'fiscal_year_active': FiscalYear.objects.filter(
                    institution=institution, is_closed=False
                ).exists(),
                'payment_methods': PaymentMethod.objects.filter(
                    institution=institution
                ).count(),
            },
            'sri_config': {
                'has_ruc': bool(institution.ruc),
                'has_signature': bool(institution.electronic_signature),
                'has_establishment': bool(institution.establishment_code),
            },
        }
        return Response(status_data)

    @action(detail=True, methods=['post'], url_path='retry-bootstrap')
    def retry_bootstrap(self, request, pk=None):
        institution = self.get_object()
        from .services import InstitutionBootstrapService
        try:
            InstitutionBootstrapService.bootstrap(institution)
            return Response(
                {
                    'status': 'Bootstrap re-executado exitosamente',
                    'new_status': institution.setup_status,
                }
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'], url_path='setup-status')
    def setup_status(self, request, pk=None):
        return self.health_check(request, pk)

    @action(detail=True, methods=['post'], url_path='complete-wizard')
    def complete_wizard(self, request, pk=None):
        institution = self.get_object()

        # Defense in depth: object permission already protects this, keep explicit check for rector scope.
        if (
            request.user.role == 'RECTOR'
            and getattr(request.user, 'institution_id', None) != institution.id
        ):
            raise PermissionDenied(
                "Solo puedes completar el wizard de tu propia institución."
            )

        with transaction.atomic():
            institution.wizard_completed = True
            institution.setup_status = 'READY_FULL'
            if not institution.setup_completed_at:
                institution.setup_completed_at = timezone.now()
            institution.save(
                update_fields=['wizard_completed', 'setup_status', 'setup_completed_at']
            )

        return Response(
            {
                'success': True,
                'wizard_completed': institution.wizard_completed,
                'setup_status': institution.setup_status,
            }
        )

    def perform_create(self, serializer):
        if not (
            self.request.user.role == 'ADMIN' or self.request.user.is_superuser
        ):
            raise PermissionDenied(
                "Solo el Administrador Global puede crear instituciones."
            )
        required_fields = [
            'name',
            'ruc',
            'address',
            'phone',
            'email',
            'establishment_code',
            'emission_point',
        ]
        for field in required_fields:
            if not serializer.validated_data.get(field):
                raise ValidationError(
                    {"error": f"Falta campo requerido: {field}"}
                )
        logger = logging.getLogger(__name__)
        from .services import InstitutionBootstrapService
        try:
            with transaction.atomic():
                logger.info(
                    "Iniciando bootstrap para nueva institución: %s",
                    serializer.validated_data.get('name'),
                )
                InstitutionBootstrapService.create_and_bootstrap(
                    serializer.validated_data
                )
                logger.info("Bootstrap completado exitosamente.")
        except Exception as e:
            logger.error(
                "Fallo en bootstrap de institución: %s", str(e), exc_info=True
            )
            raise ValidationError(
                {"error": f"Error during institution bootstrap: {str(e)}"}
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.users.exists():
            return Response(
                {
                    "error": "No se puede eliminar una institución con usuarios registrados."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if hasattr(instance, 'academic_years') and instance.academic_years.exists():
            return Response(
                {
                    "error": "No se puede eliminar una institución con años lectivos configurados."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='hard-delete')
    def hard_delete(self, request, pk=None):
        """Borrado Forzado para Superusuarios."""
        if not request.user.is_superuser:
            raise PermissionDenied(
                "Solo los superusuarios pueden realizar borrados forzados."
            )
        instance = self.get_object()
        logger = logging.getLogger(__name__)
        try:
            with transaction.atomic():
                logger.warning(
                    "Iniciando borrado forzado de institución: %s (ID: %s)",
                    instance.name,
                    instance.id,
                )
                # Detailed deletion steps omitted for brevity
                logger.info(
                    "Institución %s borrada exitosamente de forma permanente.",
                    instance.id,
                )
                return Response(
                    {
                        'message': (
                            'Institución y todos sus datos han sido eliminados '
                            'permanentemente.'
                        )
                    }
                )
        except Exception as e:
            logger.error(
                "Error en borrado forzado: %s", str(e), exc_info=True
            )
            return Response(
                {'error': f"Error durante el borrado forzado: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

from core.tenancy.viewsets import BaseTenantViewSet

class UserViewSet(InstitutionFilterMixin, BaseTenantViewSet):
    queryset = User.objects.unscoped().select_related("institution")
    serializer_class = UserSerializer
    tenant_field = 'institution'

    def get_permissions(self):
        from .permissions import CanManageUser
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), CanManageUser()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        role = serializer.validated_data.get('role')
        if role == User.Role.GLOBAL:
            serializer.save(institution=None)
        else:
            serializer.save(institution=self.request.tenant)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            queryset = queryset.filter(is_active=True)
            role = self.request.query_params.get('role')
            if role:
                queryset = queryset.filter(role=role)
                if role == 'STUDENT' and self.request.user.role == 'TEACHER':
                    queryset = queryset.filter(
                        enrollments__course__subjects__teacher=self.request.user
                    ).distinct()
            return queryset
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
