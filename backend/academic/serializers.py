from rest_framework import serializers
from .models import Course, Subject, Enrollment, Grade, Attendance, EvaluationCategory, AcademicYear, AcademicPeriod
from users.serializers import UserSerializer

class AcademicPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicPeriod
        fields = '__all__'

class AcademicYearSerializer(serializers.ModelSerializer):
    periods = AcademicPeriodSerializer(many=True, read_only=True)
    institution = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = AcademicYear
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class EvaluationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationCategory
        fields = '__all__'

class SubjectSerializer(serializers.ModelSerializer):
    evaluation_categories = EvaluationCategorySerializer(many=True, read_only=True)
    class Meta:
        model = Subject
        fields = '__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source='student', read_only=True)
    course_detail = CourseSerializer(source='course', read_only=True)
    academic_summary = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = '__all__'

    def get_academic_summary(self, obj):
        try:
            return obj.calculate_averages()
        except Exception as e:
            # print(f"Error calculating averages: {e}")
            return {}

class GradeSerializer(serializers.ModelSerializer):
    enrollment_detail = EnrollmentSerializer(source='enrollment', read_only=True)
    subject_detail = SubjectSerializer(source='subject', read_only=True)
    category_detail = EvaluationCategorySerializer(source='category', read_only=True)
    
    class Meta:
        model = Grade
        fields = '__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'
