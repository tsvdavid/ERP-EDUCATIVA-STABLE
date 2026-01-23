from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Course, Subject, Enrollment, Grade, Attendance, EvaluationCategory, AcademicYear, AcademicPeriod
from .serializers import (
    CourseSerializer, 
    SubjectSerializer, 
    EnrollmentSerializer, 
    GradeSerializer, 
    AttendanceSerializer,
    EvaluationCategorySerializer,
    AcademicYearSerializer,
    AcademicPeriodSerializer
)
from users.permissions import IsAdminUser, IsRectorUser, IsTeacherUser
from rest_framework.decorators import action
from django.db.models import Count, Case, When
from django.utils.translation import gettext_lazy as _


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    
    def perform_create(self, serializer):
        user = self.request.user
        if not user.institution:
             from rest_framework.exceptions import ValidationError
             raise ValidationError({"institution": "El usuario no tiene una institución asignada."})
        serializer.save(institution=user.institution)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), (IsAdminUser | IsRectorUser)()]
        return [permissions.IsAuthenticated()]

class AcademicPeriodViewSet(viewsets.ModelViewSet):
    queryset = AcademicPeriod.objects.all()
    serializer_class = AcademicPeriodSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), (IsAdminUser | IsRectorUser)()]
        return [permissions.IsAuthenticated()]

class CourseViewSet(viewsets.ModelViewSet):

    queryset = Course.objects.all().select_related('institution')
    serializer_class = CourseSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), (IsAdminUser | IsRectorUser)()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Course.objects.all()
        user = self.request.user
        header_inst_id = self.request.headers.get('X-Institution-ID')

        # Security: Enforce Institution
        if not user.is_superuser and user.role != 'ADMIN' and user.institution:
             queryset = queryset.filter(institution=user.institution)
             if header_inst_id and str(header_inst_id) != str(user.institution.id):
                 return queryset.none()
        elif header_inst_id:
             queryset = queryset.filter(institution_id=header_inst_id)
        
        if user.role == 'STUDENT':
             # Students only see courses they are enrolled in
             return queryset.filter(enrollments__student=user).distinct()
             
        # Admin/Superuser with no selection -> Show All
        
        # ACTIVE YEAR FILTERING
        # If no specific 'year' param is requested, default to the Institution's ACTIVE Academic Year.
        # This ensures the "Reset/Blank" experience when a new year starts.
        year_param = self.request.query_params.get('year')
        if year_param:
            queryset = queryset.filter(year=year_param)
        else:
            # Determine institution to find its active year
            target_inst_id = None
            if user.institution:
                target_inst_id = user.institution.id
            elif header_inst_id:
                target_inst_id = header_inst_id
            
            if target_inst_id:
                # Find active year for this institution
                try:
                    active_year = AcademicYear.objects.filter(institution_id=target_inst_id, is_active=True).first()
                    if active_year:
                        queryset = queryset.filter(year=active_year.year)
                except Exception:
                    pass

        return queryset

class EvaluationCategoryViewSet(viewsets.ModelViewSet):
    queryset = EvaluationCategory.objects.all()
    serializer_class = EvaluationCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = EvaluationCategory.objects.all()
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        trimester = self.request.query_params.get('trimester')
        if trimester:
            queryset = queryset.filter(trimester=trimester)
            
        return queryset

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().select_related('course', 'course__institution', 'teacher').prefetch_related('evaluation_categories')
    serializer_class = SubjectSerializer
    
    def get_permissions(self):
        # Teachers can update subjects (e.g. content), but not create/delete them (Academic Mgmt)
        if self.action in ['update', 'partial_update']:
             return [permissions.IsAuthenticated(), (IsAdminUser | IsRectorUser)()]
        if self.action in ['create', 'destroy']:
             return [permissions.IsAuthenticated(), (IsAdminUser | IsRectorUser)()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Subject.objects.all()
        user = self.request.user
        header_inst_id = self.request.headers.get('X-Institution-ID')

        # Security: Enforce Institution
        if not user.is_superuser and user.role != 'ADMIN' and user.institution:
             queryset = queryset.filter(course__institution=user.institution)
             if header_inst_id and str(header_inst_id) != str(user.institution.id):
                 return queryset.none()
        elif header_inst_id:
             queryset = queryset.filter(course__institution_id=header_inst_id)
        
        if user.role == 'TEACHER':
             queryset = queryset.filter(teacher=user)
             
        # ACTIVE YEAR FILTERING
        year_param = self.request.query_params.get('year')
        if year_param:
            queryset = queryset.filter(course__year=year_param)
        else:
            # Determine institution
            target_inst_id = None
            if user.institution:
                target_inst_id = user.institution.id
            elif header_inst_id:
                target_inst_id = header_inst_id
            
            if target_inst_id:
                try:
                    active_year = AcademicYear.objects.filter(institution_id=target_inst_id, is_active=True).first()
                    if active_year:
                        queryset = queryset.filter(course__year=active_year.year)
                except Exception:
                    pass

        return queryset

class EnrollmentViewSet(viewsets.ModelViewSet):
    # Optimize for calculate_averages() and serializers
    queryset = Enrollment.objects.all().select_related(
        'student', 
        'course', 
        'course__institution'
    ).prefetch_related(
        'grades', 
        'course__subjects', 
        'course__subjects__evaluation_categories',
        'student__children' # For UserSerializer
    )
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        header_inst_id = self.request.headers.get('X-Institution-ID')

        # Security: Enforce Institution
        if not user.is_superuser and user.role != 'ADMIN' and user.institution:
             queryset = queryset.filter(course__institution=user.institution)
             if header_inst_id and str(header_inst_id) != str(user.institution.id):
                 return queryset.none()
        elif header_inst_id:
             queryset = queryset.filter(course__institution_id=header_inst_id)
            
        if user.role == 'STUDENT':
             return queryset.filter(student=user)
        
        if user.role == 'TEACHER':
             # Teachers see students enrolled in courses they teach
             # Optimize: enrollment -> course -> subjects -> teacher = user
             return queryset.filter(course__subjects__teacher=user).distinct()
        
        # Filtering
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
            
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        # ACTIVE YEAR FILTERING
        year_param = self.request.query_params.get('year')
        if year_param:
            queryset = queryset.filter(course__year=year_param)
        else:
            # Determine institution
            target_inst_id = None
            if user.institution:
                target_inst_id = user.institution.id
            elif header_inst_id:
                target_inst_id = header_inst_id
            
            if target_inst_id:
                try:
                    active_year = AcademicYear.objects.filter(institution_id=target_inst_id, is_active=True).first()
                    if active_year:
                        queryset = queryset.filter(course__year=active_year.year)
                except Exception:
                    pass

        return queryset

    def perform_create(self, serializer):
        student = serializer.validated_data['student']
        # Check if student is already enrolled in ANY course
        if Enrollment.objects.filter(student=student).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("El estudiante ya está matriculado en un curso. Elimine la matrícula anterior para cambiarlo.")
        serializer.save()



    @action(detail=True, methods=['get'])
    def download_report_card(self, request, pk=None):
        # Optimization: Prefetch everything needed for averages
        enrollment = Enrollment.objects.select_related(
            'course', 
            'course__institution', 
            'student'
        ).prefetch_related(
            'course__subjects',
            'course__subjects__evaluation_categories',
            'grades'
        ).get(pk=pk)
        
        # Calculate fresh averages
        summary = enrollment.calculate_averages()

        try:
            # --- QUALITATIVE LOGIC ---
            def get_qualitative_score(score):
                if score >= 9: return "DA (Domina los Aprendizajes)"
                if score >= 7: return "AA (Alcanza los Aprendizajes)"
                if score >= 4: return "PA (Próximo a Alcanzar)"
                return "NA (No Alcanza los Aprendizajes)"

            # Enrich summary with qualitative data
            subjects_data = [] # For graph
            scores_data = []   # For graph

            for subject_id, data in summary.items():
                data['qualitative'] = get_qualitative_score(data['final'])
                subjects_data.append(data['name'])
                scores_data.append(data['final'])
            
            # --- GRAPH GENERATION ---
            import matplotlib
            matplotlib.use('Agg') # Force non-GUI backend
            import matplotlib.pyplot as plt
            import base64
            import io

            # Create plot
            plt.figure(figsize=(10, 4))
            bars = plt.bar(subjects_data, scores_data, color='#3498db')
            plt.ylim(0, 10)
            plt.ylabel('Calificación')
            plt.title('Rendimiento Académico')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height}',
                        ha='center', va='bottom')

            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close()
            buf.seek(0)
            image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            
            # Prepare Context
            context = {
                'enrollment': enrollment,
                'summary': summary,
                'institution': enrollment.course.institution,
                'logo_path': None,
                'chart_image': image_base64,
                'generated_at': None 
            }
            
            # Handle Logo Path for xhtml2pdf 
            if enrollment.course.institution.logo:
                try:
                    context['logo_path'] = enrollment.course.institution.logo.path
                except:
                    pass

            # Render HTML
            from django.template.loader import get_template
            from xhtml2pdf import pisa
            from django.http import HttpResponse

            template = get_template('academic/report_card_pdf.html')
            html = template.render(context)
            
            # Generate PDF
            buffer = io.BytesIO()
            pisa_status = pisa.CreatePDF(html, dest=buffer)
            
            if pisa_status.err:
                return HttpResponse(f'We had some errors <pre>{html}</pre>')
                
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Reporte_{enrollment.student.username}.pdf"'
            return response

        except Exception as e:
            print(f"Error generating PDF: {type(e)} - {e}")
            import traceback
            error_msg = traceback.format_exc()
            print(error_msg)
            
            # FORCE LOG TO FILE for debugging
            try:
                with open("view_error.txt", "w", encoding="utf-8") as f:
                    f.write(f"Error Type: {type(e)}\n")
                    f.write(f"Error: {e}\n")
                    f.write(error_msg)
            except:
                pass
                
            return HttpResponse(f"Error generando PDF: {e}", status=500)

class GradeViewSet(viewsets.ModelViewSet):
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _check_low_grade_alert(self, grade):
        if grade.score < 7:
            from communication.models import Notification
            # Check if recent notification already exists to avoid spamming (optional, but good practice)
            # For this MVP, we just create it.
            Notification.objects.create(
                user=grade.enrollment.student,
                type=Notification.Type.ALERT,
                priority=Notification.Priority.HIGH,
                title=f"Alerta Académica: {grade.subject.name}",
                message=f"Tu calificación en {grade.subject.name} ({grade.category.name if grade.category else 'General'}) es de {grade.score}. Se recomienda mejorar el rendimiento.",
                related_content_type='grade',
                related_object_id=grade.id
            )

    def perform_create(self, serializer):
        self._validate_year_period_open(serializer.validated_data)
        grade = serializer.save()
        self._check_low_grade_alert(grade)

    def perform_update(self, serializer):
        self._validate_year_period_open(serializer.validated_data)
        grade = serializer.save()
        self._check_low_grade_alert(grade)

    def _validate_year_period_open(self, validated_data):
        # Allow specific roles to bypass? For now, stricty block modifications as requested.
        
        # Get related context
        instance = None
        if self.action in ['update', 'partial_update']:
            instance = self.get_object()
        
        # Determine enrollment and category
        enrollment = validated_data.get('enrollment') or (instance.enrollment if instance else None)
        category = validated_data.get('category') or (instance.category if instance else None)
        
        if not enrollment or not category:
            return

        course = enrollment.course
        year_val = course.year
        institution_id = course.institution_id
        
        # Check Academic Year Status
        try:
            acad_year = AcademicYear.objects.get(year=year_val, institution_id=institution_id)
            if acad_year.is_closed:
                from rest_framework.exceptions import ValidationError
                raise ValidationError(_("El Año Lectivo está cerrado. No se pueden modificar calificaciones."))
        except AcademicYear.DoesNotExist:
            pass

        # Check Academic Period Status
        if 'acad_year' in locals():
            trimester_num = category.trimester 
            try:
                period = acad_year.periods.get(number=trimester_num)
                if period.is_closed:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError(_(f"El Trimestre {trimester_num} está cerrado. No se pueden modificar calificaciones."))
            except AcademicPeriod.DoesNotExist:
                pass


    def get_queryset(self):
        queryset = Grade.objects.all().select_related(
            'enrollment', 
            'enrollment__student', 
            'subject', 
            'category',
            'enrollment__course'
        )
        user = self.request.user
        header_inst_id = self.request.headers.get('X-Institution-ID')

        # Security: Enforce Institution
        if not user.is_superuser and user.role != 'ADMIN' and user.institution:
             queryset = queryset.filter(enrollment__course__institution=user.institution)
             if header_inst_id and str(header_inst_id) != str(user.institution.id):
                 return queryset.none()
        elif header_inst_id:
             queryset = queryset.filter(enrollment__course__institution_id=header_inst_id)

        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(enrollment__student_id=student_id)
        
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
            
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(enrollment__course_id=course_id)
        
        # Seurity: Parents/Students can only see their own data
        if user.role == 'STUDENT':
            queryset = queryset.filter(enrollment__student=user)
        elif user.role == 'PARENT':
             queryset = queryset.filter(enrollment__student__in=user.children.all())
             
        # ACTIVE YEAR FILTERING
        year_param = self.request.query_params.get('year')
        if year_param:
            queryset = queryset.filter(enrollment__course__year=year_param)
        else:
            # Determine institution
            target_inst_id = None
            if user.institution:
                target_inst_id = user.institution.id
            elif header_inst_id:
                target_inst_id = header_inst_id
            
            if target_inst_id:
                try:
                    active_year = AcademicYear.objects.filter(institution_id=target_inst_id, is_active=True).first()
                    # Only filter if active year exists. 
                    # If we have a course_id or subject_id specific query, we might arguably SKIP this 
                    # to avoid 404ing old data, but for "Clean Slate" we enforce it unless requested.
                    # HOWEVER, preventing 404s on direct ID access might be nice?
                    # For now, strict enforcement requires ?year=...
                    if active_year:
                        queryset = queryset.filter(enrollment__course__year=active_year.year)
                except Exception:
                    pass

        return queryset

class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Attendance.objects.all().select_related('enrollment', 'enrollment__student')
        user = self.request.user
        header_inst_id = self.request.headers.get('X-Institution-ID')

        # Security: Enforce Institution
        if not user.is_superuser and user.role != 'ADMIN' and user.institution:
             queryset = queryset.filter(enrollment__course__institution=user.institution)
             if header_inst_id and str(header_inst_id) != str(user.institution.id):
                 return queryset.none()
        elif header_inst_id:
             queryset = queryset.filter(enrollment__course__institution_id=header_inst_id)

        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(enrollment__student_id=student_id)

        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(enrollment__course_id=course_id)
            
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)

        if user.role == 'STUDENT':
            queryset = queryset.filter(enrollment__student=user)
        elif user.role == 'PARENT':
             queryset = queryset.filter(enrollment__student__in=user.children.all())
        elif user.role == 'TEACHER':
             queryset = queryset.filter(enrollment__course__subjects__teacher=user).distinct()

        # ACTIVE YEAR FILTERING
        year_param = self.request.query_params.get('year')
        if year_param:
            queryset = queryset.filter(enrollment__course__year=year_param)
        else:
            # Determine institution
            target_inst_id = None
            if user.institution:
                target_inst_id = user.institution.id
            elif header_inst_id:
                target_inst_id = header_inst_id
            
            if target_inst_id:
                try:
                    active_year = AcademicYear.objects.filter(institution_id=target_inst_id, is_active=True).first()
                    if active_year:
                        queryset = queryset.filter(enrollment__course__year=active_year.year)
                except Exception:
                    pass

        return queryset

    @action(detail=False, methods=['get'], url_path='report')
    def report(self, request):
        """
        Custom endpoint to generate attendance report.
        Query Params:
        - course_id (required)
        - start_date (optional)
        - end_date (optional)
        """
        course_id = request.query_params.get('course_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not course_id:
            return Response({"error": "course_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Filters for the annotation
        from django.db.models import Count, Q
        
        # Build the dynamic filter for the related objects
        date_filter = Q()
        if start_date:
            date_filter &= Q(attendance_records__date__gte=start_date)
        if end_date:
            date_filter &= Q(attendance_records__date__lte=end_date)

        # Optimize using annotation on the Enrollments directly
        # We filter the enrollment by course, then annotate counts based on the related attendance_records
        enrollments = Enrollment.objects.filter(course_id=course_id).select_related('student').annotate(
            present_count=Count('attendance_records', filter=date_filter & Q(attendance_records__status='PRESENT')),
            absent_count=Count('attendance_records', filter=date_filter & Q(attendance_records__status='ABSENT')),
            late_count=Count('attendance_records', filter=date_filter & Q(attendance_records__status='LATE')),
            excused_count=Count('attendance_records', filter=date_filter & Q(attendance_records__status='EXCUSED')),
            total_count=Count('attendance_records', filter=date_filter)
        )
            
        data = []
        for enrollment in enrollments:
            total = enrollment.total_count
            # percentage = (Total - Absent) / Total
            if total > 0:
                valid_attendance = total - enrollment.absent_count
                percentage = round((valid_attendance / total) * 100, 2)
            else:
                percentage = 100.0 
                
            data.append({
                "student_id": enrollment.student.id,
                "student_name": f"{enrollment.student.first_name} {enrollment.student.last_name}",
                "present": enrollment.present_count,
                "absent": enrollment.absent_count,
                "late": enrollment.late_count,
                "excused": enrollment.excused_count,
                "total_days": total,
                "percentage": percentage
            })
            
        return Response(data)

