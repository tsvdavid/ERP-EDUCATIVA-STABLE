from rest_framework import serializers
from ..models import Module, Lesson, LearningResource

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
            'duration_minutes', 'order', 'resources', 'is_completed',
            'meeting_url', 'meeting_date'
        ]

class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    quiz = serializers.SerializerMethodField()
    assignments = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'description', 'order', 'lessons', 'quiz', 'assignments']

    def get_quiz(self, obj):
        from .quiz import QuizSerializer
        # The model has related_name='quizzes'
        quiz = obj.quizzes.first()
        if quiz:
            return QuizSerializer(quiz).data
        return None

    def get_assignments(self, obj):
        from .assignment import AssignmentSerializer
        return AssignmentSerializer(obj.assignments.all(), many=True).data
