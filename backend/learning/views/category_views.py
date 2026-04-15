from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from ..models import CourseGroup, CourseTag
from ..serializers.course import CourseGroupSerializer, CourseTagSerializer

class CourseGroupViewSet(viewsets.ModelViewSet):
    queryset = CourseGroup.objects.all()
    serializer_class = CourseGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.institution:
            return self.queryset.filter(institution=user.institution)
        return self.queryset.all()
    
    def perform_create(self, serializer):
        # Always use the authenticated user's institution
        institution = self.request.user.institution
        serializer.save(institution=institution)

class CourseTagViewSet(viewsets.ModelViewSet):
    queryset = CourseTag.objects.all()
    serializer_class = CourseTagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.request.query_params.get('group')
        qs = self.queryset
        if group_id:
            qs = qs.filter(group_id=group_id)
        # Filter by institution via group
        user = self.request.user
        if user.institution:
            qs = qs.filter(group__institution=user.institution)
        return qs
