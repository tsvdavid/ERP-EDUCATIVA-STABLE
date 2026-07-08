from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from ..models import Assignment, AssignmentSubmission
from ..serializers import AssignmentSerializer, AssignmentSubmissionSerializer
from users.tenant_mixins import InstitutionFilterMixin

class AssignmentViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_lookup = 'module__course__institution'

    def get_queryset(self):
        return super().get_queryset()

class AssignmentSubmissionViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = AssignmentSubmission.objects.all()
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_lookup = 'assignment__module__course__institution'

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        assignment_id = self.request.query_params.get('assignment')
        if assignment_id:
            queryset = queryset.filter(assignment_id=assignment_id)

        if user.role in ['ADMIN', 'RECTOR', 'LOCAL_ADMIN']:
            return queryset.filter(assignment__module__course__institution=user.institution)
        
        if user.role == 'TEACHER':
            return queryset.filter(assignment__module__course__instructor=user)
        
        return queryset.filter(student=user)

    def perform_create(self, serializer):
        assignment = serializer.validated_data['assignment']
        tenant = getattr(self.request, 'tenant', None)
        if not tenant or assignment.module.course.institution_id != tenant.id:
            raise ValidationError('Assignment fuera del tenant activo')
        # If student already has a submission for this assignment, update it
        existing = AssignmentSubmission.objects.filter(assignment=assignment, student=self.request.user).first()
        if existing:
            serializer.instance = existing
        serializer.save(student=self.request.user, submitted_at=timezone.now())
