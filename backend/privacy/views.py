from rest_framework import viewsets, permissions, status, serializers

from .models import PolicyVersion, ConsentRecord, ARCORequest, TreatmentActivity, DataBreach
from .serializers import (
    PolicyVersionSerializer,
    ConsentRecordSerializer,
    ARCORequestSerializer,
    TreatmentActivitySerializer,
    DataBreachSerializer
)
from django.db.models import Q
from users.models import Institution
from users.permissions import IsAdminUser, IsLocalAdminUser

class PolicyVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PolicyVersion.objects.filter(is_active=True).order_by('-published_at')
    serializer_class = PolicyVersionSerializer
    permission_classes = [permissions.AllowAny] # Publicly viewable

class ConsentRecordViewSet(viewsets.ModelViewSet):
    serializer_class = ConsentRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ConsentRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Capture metadata
        ip = self.request.META.get('REMOTE_ADDR')
        agent = self.request.META.get('HTTP_USER_AGENT', '')
        serializer.save(
            user=self.request.user,
            ip_address=ip,
            user_agent=agent
        )

from django.db.models import Q
from users.models import Institution

class ARCORequestViewSet(viewsets.ModelViewSet):
    serializer_class = ARCORequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Optimize query
        base_qs = ARCORequest.objects.select_related('institution', 'requester')

        # 1. Superusers always see everything
        if user.is_superuser:
            return base_qs

        # 2. Admins and Rectors see their institution's requests
        if user.role in ['ADMIN', 'RECTOR']: 
            if user.institution:
                # Show requests from their institution OR their own personal requests
                qs = base_qs.filter(Q(institution=user.institution) | Q(requester=user))
                return qs.distinct()
            
        # 3. Everyone else (Student, Parent, Teacher) OR Admins without institution
        # only see their own requests.
        return base_qs.filter(requester=user)

    def perform_create(self, serializer):
        institution = self.request.user.institution
        if not institution:
            # BLOQUEO: Ya no permitimos fallback a Institution.objects.first()
            # Esto evita que peticiones de privacidad se asignen a la institución equivocada
            raise serializers.ValidationError({"institution": "No hay una institución asociada a su cuenta de usuario."})

        serializer.save(institution=institution, requester=self.request.user)

class TreatmentActivityViewSet(viewsets.ModelViewSet):
    serializer_class = TreatmentActivitySerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        return TreatmentActivity.objects.filter(institution=self.request.user.institution)

class DataBreachViewSet(viewsets.ModelViewSet):
    serializer_class = DataBreachSerializer
    permission_classes = [permissions.IsAdminUser] # Only admins can manage breach records
    
    def get_queryset(self):
        return DataBreach.objects.filter(institution=self.request.user.institution)
