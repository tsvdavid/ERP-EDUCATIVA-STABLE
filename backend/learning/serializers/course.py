from users.models import Institution, User
from rest_framework import serializers
from ..models import LMSCourse, LMSEnrollment, LessonProgress, CourseGroup, CourseTag

class CourseGroupSerializer(serializers.ModelSerializer):
    institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(), required=False, allow_null=True
    )
    class Meta:
        model = CourseGroup
        fields = ['id', 'institution', 'name', 'description', 'icon', 'created_at']
        extra_kwargs = {
            "institution": {"required": False, "allow_null": True}
        }

class CourseTagSerializer(serializers.ModelSerializer):
    group_name = serializers.ReadOnlyField(source='group.name')
    class Meta:
        model = CourseTag
        fields = ['id', 'group', 'group_name', 'name', 'description', 'created_at']
from .content import ModuleSerializer

class CourseSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    enrollment_count = serializers.IntegerField(source='enrollments.count', read_only=True)
    institution = serializers.PrimaryKeyRelatedField(queryset=Institution.objects.all(), default=1)
    instructor = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='TEACHER'), default=1)
    
    # Metadatos Académicos
    academic_course_id = serializers.IntegerField(source='subject.course.id', read_only=True)
    academic_course_name = serializers.CharField(source='subject.course.name', read_only=True)
    academic_parallel = serializers.CharField(source='subject.course.parallel', read_only=True)
    academic_year = serializers.IntegerField(source='subject.course.year', read_only=True)
    
    # Categorización (Group & Tag)
    group_id = serializers.IntegerField(source='tag.group.id', read_only=True)
    group_name = serializers.CharField(source='tag.group.name', read_only=True)
    tag_name = serializers.CharField(source='tag.name', read_only=True)
    tag_id = serializers.PrimaryKeyRelatedField(
        queryset=CourseTag.objects.all(), 
        source='tag', 
        required=False, 
        allow_null=True
    )
    
    class Meta:
        model = LMSCourse
        fields = [
            'id', 'institution', 'instructor', 'instructor_name', 'title', 'subject',
            'subtitle', 'description', 'cover_image', 'price', 'discount_price',
            'is_public', 'ai_summary', 'ai_keywords', 'is_active', 'created_at',
            'modules', 'enrollment_count', 'academic_course_id', 'academic_course_name', 
            'academic_parallel', 'academic_year', 'tag_id', 'group_id', 
            'group_name', 'tag_name'
        ]

class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    student_name = serializers.SerializerMethodField()
    student_email = serializers.CharField(source='user.email', read_only=True)
    last_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = LMSEnrollment
        fields = [
            'id', 'user', 'course', 'course_title', 
            'student_name', 'student_email', 'enrolled_at', 
            'progress_percentage', 'is_completed', 'status', 'last_activity'
        ]

    def get_student_name(self, obj):
        full_name = obj.user.get_full_name()
        return full_name if full_name else obj.user.username

    def get_last_activity(self, obj):
        from ..models import LessonProgress
        last_lp = LessonProgress.objects.filter(enrollment=obj).order_by('-last_accessed').first()
        return last_lp.last_accessed if last_lp else None

class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = '__all__'
