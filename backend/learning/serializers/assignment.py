from rest_framework import serializers
from ..models import Assignment, AssignmentSubmission

class AssignmentSerializer(serializers.ModelSerializer):
    my_submission = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'module', 'title', 'description', 
            'due_date', 'max_score', 'attachment', 
            'my_submission', 'academic_category'
        ]

    def get_my_submission(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            submission = AssignmentSubmission.objects.filter(assignment=obj, student=request.user).first()
            if submission:
                return AssignmentSubmissionSerializer(submission).data
        return None

class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    
    class Meta:
        model = AssignmentSubmission
        fields = [
            'id', 'assignment', 'student', 'student_name', 'file', 
            'submitted_at', 'score', 'teacher_feedback', 'graded_at'
        ]
        read_only_fields = ['student']
        # Remove unique_together validator to handle it in perform_create (update or create)
        validators = []
