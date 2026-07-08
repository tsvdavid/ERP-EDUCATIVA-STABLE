from rest_framework import viewsets, permissions, status, serializers
from rest_framework.exceptions import ValidationError

from .models import PolicyVersion, ConsentRecord, ARCORequest, TreatmentActivity, DataBreach
from .serializers import (
    PolicyVersionSerializer,
    ConsentRecordSerializer,
    ARCORequestSerializer,
    TreatmentActivitySerializer,
    DataBreachSerializer
)
from users.permissions import IsAdminUser, IsLocalAdminUser

class PolicyVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PolicyVersion.objects.filter(is_active=True).order_by('-published_at')
    serializer_class = PolicyVersionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return self.queryset.none()
        return self.queryset.filter(institution=tenant)

class ConsentRecordViewSet(viewsets.ModelViewSet):
    serializer_class = ConsentRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return ConsentRecord.objects.none()
        return ConsentRecord.objects.filter(user=self.request.user, institution=tenant)

    def perform_create(self, serializer):
        # Capture metadata
        ip = self.request.META.get('REMOTE_ADDR')
        agent = self.request.META.get('HTTP_USER_AGENT', '')
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            raise ValidationError('No se pudo determinar el tenant activo.')
        serializer.save(
            institution=tenant,
            user=self.request.user,
            ip_address=ip,
            user_agent=agent
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        serializer.save(institution=instance.institution, user=instance.user)

class ARCORequestViewSet(viewsets.ModelViewSet):
    serializer_class = ARCORequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return ARCORequest.objects.none()

        base_qs = ARCORequest.objects.select_related('institution', 'requester')

        if user.role in ['ADMIN', 'RECTOR', 'LOCAL_ADMIN'] or user.is_superuser:
            return base_qs.filter(institution=tenant)

        return base_qs.filter(requester=user, institution=tenant)

    def perform_create(self, serializer):
        institution = getattr(self.request, 'tenant', None)
        if not institution:
            raise serializers.ValidationError({"institution": "No se pudo determinar el tenant activo."})

        serializer.save(institution=institution, requester=self.request.user)

class TreatmentActivityViewSet(viewsets.ModelViewSet):
    serializer_class = TreatmentActivitySerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return TreatmentActivity.objects.none()
        return TreatmentActivity.objects.filter(institution=tenant)

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            raise ValidationError('No se pudo determinar el tenant activo.')
        serializer.save(institution=tenant)

    def perform_update(self, serializer):
        instance = serializer.instance
        serializer.save(institution=instance.institution)

class DataBreachViewSet(viewsets.ModelViewSet):
    serializer_class = DataBreachSerializer
    permission_classes = [permissions.IsAdminUser] # Only admins can manage breach records
    
    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return DataBreach.objects.none()
        return DataBreach.objects.filter(institution=tenant)

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            raise ValidationError('No se pudo determinar el tenant activo.')
        serializer.save(institution=tenant)

    def perform_update(self, serializer):
        instance = serializer.instance
        serializer.save(institution=instance.institution)
