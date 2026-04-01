from rest_framework import serializers
from .models import (
    LMSCourse, Module, Lesson, LearningResource, LMSEnrollment, 
    LessonProgress, Quiz, Question, Choice, QuizAttempt, AnswerSubmission
)

class LearningResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningResource
        fields = '__all__'

class LessonSerializer(serializers.ModelSerializer):
    resources = LearningResourceSerializer(many=True, read_only=True)
    is_completed = serializers.BooleanField(read_only=True, default=False)
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'module', 'title', 'content', 'video_url', 
            'duration_minutes', 'order', 'resources', 'is_completed'
        ]

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'question', 'text', 'is_correct']

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'text', 'question_type', 'points', 'order', 'choices']

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'module', 'title', 'description', 'passing_score', 
            'time_limit_minutes', 'is_active', 'created_at', 'questions'
        ]

class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    quiz = QuizSerializer(many=False, read_only=True)
    
    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'description', 'order', 'lessons', 'quiz']

class CourseSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    enrollment_count = serializers.IntegerField(source='enrollments.count', read_only=True)
    institution = serializers.PrimaryKeyRelatedField(read_only=True)
    instructor = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = LMSCourse
        fields = [
            'id', 'institution', 'instructor', 'instructor_name', 'title', 
            'subtitle', 'description', 'cover_image', 'price', 'discount_price',
            'is_public', 'ai_summary', 'ai_keywords', 'is_active', 'created_at',
            'modules', 'enrollment_count'
        ]

class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = LMSEnrollment
        fields = '__all__'

class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = '__all__'

class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = '__all__'

class AnswerSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerSubmission
        fields = '__all__'
