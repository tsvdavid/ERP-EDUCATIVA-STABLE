from decimal import Decimal
from django.db import models
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    LMSCourse, Module, Lesson, LearningResource, LMSEnrollment, 
    LessonProgress, Quiz, Question, Choice, QuizAttempt, AnswerSubmission
)
from .serializers import (
    CourseSerializer, ModuleSerializer, LessonSerializer, 
    LearningResourceSerializer, EnrollmentSerializer, LessonProgressSerializer,
    QuizSerializer, QuestionSerializer, ChoiceSerializer, 
    QuizAttemptSerializer, AnswerSubmissionSerializer
)

class CourseViewSet(viewsets.ModelViewSet):
    queryset = LMSCourse.objects.all()
    serializer_class = CourseSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # Internal or Public courses
            return self.queryset.filter(models.Q(institution=user.institution) | models.Q(is_public=True))
        # Only public courses for guests
        return self.queryset.filter(is_public=True)

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

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = LMSEnrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

class LearningResourceViewSet(viewsets.ModelViewSet):
    queryset = LearningResource.objects.all()
    serializer_class = LearningResourceSerializer

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

class ChoiceViewSet(viewsets.ModelViewSet):
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer

class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def submit_answers(self, request, pk=None):
        attempt = self.get_object()
        if attempt.completed_at:
            return Response({'error': 'Quiz already submitted'}, status=status.HTTP_400_BAD_REQUEST)
        
        answers = request.data.get('answers', []) # List of {question_id: X, choice_id: Y}
        
        total_points = 0
        earned_points = 0
        
        # Calculate total possible points first
        total_points = sum(q.points for q in attempt.quiz.questions.all())
        
        for ans in answers:
            try:
                question = Question.objects.get(id=ans['question_id'], quiz=attempt.quiz)
                choice = Choice.objects.get(id=ans['choice_id'], question=question)
                
                AnswerSubmission.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_choice=choice
                )
                
                if choice.is_correct:
                    earned_points += question.points
            except (Question.DoesNotExist, Choice.DoesNotExist):
                continue
        
        # Calculate score percentage
        score = (earned_points * 100 / total_points) if total_points > 0 else 0
        attempt.score = score
        attempt.is_passed = score >= attempt.quiz.passing_score
        from django.utils import timezone
        attempt.completed_at = timezone.now()
        attempt.save()
        
        return Response({
            'score': score.quantize(Decimal('0.01')) if hasattr(score, 'quantize') else round(float(score), 2),
            'is_passed': attempt.is_passed
        }, status=status.HTTP_200_OK)
