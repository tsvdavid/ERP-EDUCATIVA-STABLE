from django.db import models
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import LMSCourse, LMSEnrollment
from ..serializers import CourseSerializer, EnrollmentSerializer

class CourseViewSet(viewsets.ModelViewSet):
    queryset = LMSCourse.objects.all()
    serializer_class = CourseSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        
        # Filtros por Query Params
        course_id = self.request.query_params.get('course_id')
        subject_id = self.request.query_params.get('subject_id')
        search_query = self.request.query_params.get('search')

        if course_id:
            queryset = queryset.filter(subject__course_id=course_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if search_query:
            queryset = queryset.filter(models.Q(title__icontains=search_query) | models.Q(description__icontains=search_query))

        if not user.is_authenticated:
            return queryset.filter(is_public=True)
            
        if user.role == 'ADMIN':
            return queryset.filter(institution=user.institution)
            
        if user.role == 'TEACHER':
            return queryset.filter(
                models.Q(instructor=user) | 
                models.Q(subject__teacher=user)
            ).distinct()
            
        if user.role == 'STUDENT':
            # Estudiantes ven cursos públicos O cursos donde ya están matriculados
            return queryset.filter(
                models.Q(is_public=True) | models.Q(enrollments__user=user),
                is_active=True
            ).distinct()
            
        return queryset.filter(is_public=True)

    def perform_create(self, serializer):
        serializer.save(
            institution=self.request.user.institution,
            instructor=self.request.user
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, pk=None):
        course = self.get_object()
        user = request.user
        enrollment, created = LMSEnrollment.objects.get_or_create(user=user, course=course)
        if created:
            return Response({'status': 'enrolled'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'already enrolled'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def sync_students(self, request, pk=None):
        """
        Sincroniza manualmente los alumnos del curso académico con el aula virtual.
        """
        lms_course = self.get_object()
        user = request.user
        
        if user.role not in ['ADMIN', 'TEACHER']:
            return Response({'error': 'No tienes permisos para sincronizar alumnos.'}, status=status.HTTP_403_FORBIDDEN)
            
        if not lms_course.subject:
            return Response({'error': 'Esta aula no está vinculada a una materia académica.'}, status=status.HTTP_400_BAD_REQUEST)
            
        from academic.models import Enrollment as AcademicEnrollment
        academic_enrollments = AcademicEnrollment.objects.filter(course=lms_course.subject.course)
        
        created_count = 0
        for acad_enr in academic_enrollments:
            _, created = LMSEnrollment.objects.get_or_create(
                user=acad_enr.student,
                course=lms_course,
                defaults={'status': 'active'}
            )
            if created:
                created_count += 1
                
        return Response({
            'status': 'success',
            'new_enrollments': created_count,
            'total_enrollments': lms_course.enrollments.count()
        }, status=status.HTTP_200_OK)

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = LMSEnrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return self.queryset.none()
        
        if user.role in ['ADMIN', 'TEACHER']:
            # Pueden ver todas las inscripciones de su institución
            queryset = self.queryset.filter(course__institution=user.institution)
            course_id = self.request.query_params.get('course_id')
            if course_id:
                queryset = queryset.filter(course_id=course_id)
            return queryset
        
        # Alumnos solo ven las suyas
        return self.queryset.filter(user=user)
