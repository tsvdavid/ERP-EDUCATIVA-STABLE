from rest_framework import serializers
from .models import (
    MedicalRecord, MedicalVisit, DeceRecord, DeceVisit,
    BehaviorRecord, BehaviorCase, CaseFollowUp,
    StudentRiskProfile, AlertRule
)
from users.serializers import UserSerializer


class MedicalRecordSerializer(serializers.ModelSerializer):
    student_details = UserSerializer(source='student', read_only=True)

    class Meta:
        model = MedicalRecord
        fields = '__all__'


class MedicalVisitSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)

    class Meta:
        model = MedicalVisit
        fields = '__all__'


class DeceRecordSerializer(serializers.ModelSerializer):
    student_details = UserSerializer(source='student', read_only=True)

    class Meta:
        model = DeceRecord
        fields = '__all__'


class DeceVisitSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    counselor_name = serializers.CharField(source='counselor.get_full_name', read_only=True)

    class Meta:
        model = DeceVisit
        fields = '__all__'


# ===== BEHAVIORAL TRACKING SERIALIZERS =====

class BehaviorRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    record_type_display = serializers.CharField(source='get_record_type_display', read_only=True)
    template_display = serializers.CharField(source='get_template_display', read_only=True)
    course_name = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source='subject.name', read_only=True, default=None)

    class Meta:
        model = BehaviorRecord
        fields = '__all__'

    def get_course_name(self, obj):
        if obj.course:
            return f"{obj.course.name} {obj.course.parallel}"
        return None


class CaseFollowUpSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    follow_up_type_display = serializers.CharField(source='get_follow_up_type_display', read_only=True)

    class Meta:
        model = CaseFollowUp
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        # Docentes y padres no ven notas confidenciales
        if request and hasattr(request, 'user'):
            if request.user.role in ['TEACHER', 'PARENT', 'STUDENT']:
                if instance.is_confidential:
                    data['content'] = '[Información confidencial - Solo DECE/Médico]'
                    data['agreements'] = ''
                    data['attachment'] = None
        return data


class BehaviorCaseSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_detail = UserSerializer(source='student', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, default=None)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, default=None)
    area_display = serializers.CharField(source='get_area_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    follow_ups = CaseFollowUpSerializer(many=True, read_only=True)
    follow_up_count = serializers.SerializerMethodField()

    class Meta:
        model = BehaviorCase
        fields = '__all__'

    def get_follow_up_count(self, obj):
        return obj.follow_ups.count()


class BehaviorCaseSummarySerializer(serializers.ModelSerializer):
    """Versión ligera para listados."""
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    area_display = serializers.CharField(source='get_area_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    follow_up_count = serializers.SerializerMethodField()

    class Meta:
        model = BehaviorCase
        fields = [
            'id', 'student', 'student_name', 'area', 'area_display',
            'status', 'status_display', 'priority', 'priority_display',
            'title', 'created_at', 'updated_at', 'follow_up_count'
        ]

    def get_follow_up_count(self, obj):
        return obj.follow_ups.count()


class StudentRiskProfileSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_detail = UserSerializer(source='student', read_only=True)
    overall_risk_display = serializers.CharField(source='get_overall_risk_display', read_only=True)

    class Meta:
        model = StudentRiskProfile
        fields = '__all__'


class AlertRuleSerializer(serializers.ModelSerializer):
    target_area_display = serializers.CharField(source='get_target_area_display', read_only=True)

    class Meta:
        model = AlertRule
        fields = '__all__'
        read_only_fields = ['institution']
