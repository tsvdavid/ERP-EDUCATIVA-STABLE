from rest_framework import serializers
from .models import ProcedureTemplate, StudentRequest
from users.serializers import UserSerializer

class ProcedureTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureTemplate
        fields = '__all__'
        read_only_fields = ['institution', 'created_at']


class StudentRequestSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_description = serializers.CharField(source='template.description', read_only=True)
    approver_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    generated_file = serializers.SerializerMethodField()

    class Meta:
        model = StudentRequest
        fields = '__all__'
        read_only_fields = ['institution', 'student', 'status', 'request_date', 'approved_by', 'approval_date', 'response_notes', 'generated_file']

    def get_generated_file(self, obj):
        if obj.generated_file:
            return obj.generated_file.url
        return None

class StudentRequestActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['APPROVE', 'REJECT'])
    notes = serializers.CharField(required=False, allow_blank=True)
