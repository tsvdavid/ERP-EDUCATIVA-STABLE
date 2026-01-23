from rest_framework import viewsets, permissions, status

from .models import PolicyVersion, ConsentRecord, ARCORequest, TreatmentActivity, DataBreach
from .serializers import (
    PolicyVersionSerializer,
    ConsentRecordSerializer,
    ARCORequestSerializer,
    TreatmentActivitySerializer,
    DataBreachSerializer
)

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

        if user.role == 'ADMIN': 
            # Allow admins to see requests for their institution OR their own personal requests
            qs = base_qs
            
            # Filter by institution if available, otherwise just personal
            if user.institution:
                qs = qs.filter(Q(institution=user.institution) | Q(requester=user))
            else:
                # If admin has no institution, they can only see their own requests (or fallback inst if we want)
                # For safety/clarity, ensure they always see their own.
                qs = qs.filter(requester=user)
                
            return qs.distinct()
        return base_qs.filter(requester=user)

    def perform_create(self, serializer):
        institution = self.request.user.institution
        if not institution:
            # Fallback: try to find the first available institution (common in dev/single-tenant)
            institution = Institution.objects.first()
            
        if not institution:
            # If still no institution, we can't create the request
            raise serializers.ValidationError({"institution": "No institution associated with this user."})

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
