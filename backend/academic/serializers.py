from rest_framework import serializers
from .models import Course, Subject, Enrollment, Grade, Attendance, EvaluationCategory, AcademicYear, AcademicPeriod, ClassSchedule, Observation
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
        fields = ('id', 'subject', 'name', 'weight', 'trimester')

class SubjectSerializer(serializers.ModelSerializer):
    # evaluation_categories = EvaluationCategorySerializer(many=True, read_only=True)
    class Meta:
        model = Subject
        fields = '__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source='student', read_only=True)
    course_detail = CourseSerializer(source='course', read_only=True)
    academic_summary = serializers.SerializerMethodField()
    attendance_summary = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = '__all__'

    def get_academic_summary(self, obj):
        try:
            return obj.calculate_averages()
        except Exception as e:
            return {}

    def get_attendance_summary(self, obj):
        try:
            records = obj.attendance_records.all()
            total = records.count()
            if total == 0:
                return {
                    'total_classes': 0, 'present': 0, 'absent': 0,
                    'late': 0, 'excused': 0, 'percentage': 100.0
                }
            
            p = records.filter(status='PRESENT').count()
            a = records.filter(status='ABSENT').count()
            l = records.filter(status='LATE').count()
            e = records.filter(status='EXCUSED').count()
            
            attended = p + l + e 
            percentage = round((attended / total) * 100, 2)
            
            return {
                'total_classes': total,
                'present': p,
                'absent': a,
                'late': l,
                'excused': e,
                'percentage': percentage
            }
        except Exception as e:
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

class ClassScheduleSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='subject.teacher.get_full_name', read_only=True)
    course_id = serializers.IntegerField(source='subject.course_id', read_only=True)

    class Meta:
        model = ClassSchedule
        fields = '__all__'

class ObservationSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source='student', read_only=True)
    teacher_detail = UserSerializer(source='teacher', read_only=True)

    class Meta:
        model = Observation
        fields = '__all__'
