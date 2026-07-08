from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from ..models import CourseGroup, CourseTag
from ..serializers.course import CourseGroupSerializer, CourseTagSerializer
from users.tenant_mixins import InstitutionFilterMixin
from rest_framework.exceptions import ValidationError

class CourseGroupViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = CourseGroup.objects.all()
    serializer_class = CourseGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = 'institution'
    
    def get_queryset(self):
        return super().get_queryset()
    
    def perform_create(self, serializer):
        institution = getattr(self.request, 'tenant', None)
        if not institution:
            raise ValidationError('No se pudo determinar el tenant activo.')
        serializer.save(institution=institution)

class CourseTagViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = CourseTag.objects.all()
    serializer_class = CourseTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_lookup = 'group__institution'

    def get_queryset(self):
        group_id = self.request.query_params.get('group')
        qs = super().get_queryset()
        if group_id:
            qs = qs.filter(group_id=group_id)
        return qs
