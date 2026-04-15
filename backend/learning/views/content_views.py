from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Module, Lesson, LearningResource, LMSEnrollment, LessonProgress
from ..serializers import ModuleSerializer, LessonSerializer, LearningResourceSerializer, LessonProgressSerializer

class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def complete(self, request, pk=None):
        lesson = self.get_object()
        user = request.user
        try:
            enrollment = LMSEnrollment.objects.get(user=user, course=lesson.module.course)
            progress, created = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
            progress.is_completed = True
            progress.save()
            
            # Recalculate course progress
            total_lessons = Lesson.objects.filter(module__course=lesson.module.course).count()
            completed_lessons = LessonProgress.objects.filter(enrollment=enrollment, is_completed=True).count()
            
            enrollment.progress_percentage = (completed_lessons * 100 / total_lessons) if total_lessons > 0 else 0
            if enrollment.progress_percentage == 100:
                enrollment.status = 'completed'
                enrollment.is_completed = True
            enrollment.save()
            
            return Response({'progress': enrollment.progress_percentage}, status=status.HTTP_200_OK)
        except LMSEnrollment.DoesNotExist:
            return Response({'error': 'Not enrolled in this course'}, status=status.HTTP_400_BAD_REQUEST)

class LearningResourceViewSet(viewsets.ModelViewSet):
    queryset = LearningResource.objects.all()
    serializer_class = LearningResourceSerializer

class LessonProgressViewSet(viewsets.ModelViewSet):
    queryset = LessonProgress.objects.all()
    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
