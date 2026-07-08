from decimal import Decimal
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from ..models import Quiz, Question, Choice, QuizAttempt, AnswerSubmission
from ..serializers import QuizSerializer, QuestionSerializer, ChoiceSerializer, QuizAttemptSerializer, AnswerSubmissionSerializer
from users.tenant_mixins import InstitutionFilterMixin

class QuizViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_lookup = 'module__course__institution'

class QuestionViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_lookup = 'quiz__module__course__institution'

class ChoiceViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_lookup = 'question__quiz__module__course__institution'

class QuizAttemptViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_lookup = 'quiz__module__course__institution'

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def submit_answers(self, request, pk=None):
        attempt = self.get_object()
        if attempt.completed_at:
            return Response({'error': 'Quiz already submitted'}, status=status.HTTP_400_BAD_REQUEST)
        
        answers = request.data.get('answers', [])
        total_points = sum(q.points for q in attempt.quiz.questions.all())
        earned_points = 0
        
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
        
        score = (earned_points * 100 / total_points) if total_points > 0 else 0
        attempt.score = score
        attempt.is_passed = score >= attempt.quiz.passing_score
        attempt.completed_at = timezone.now()
        attempt.save()
        
        return Response({
            'score': round(float(score), 2),
            'is_passed': attempt.is_passed
        }, status=status.HTTP_200_OK)
