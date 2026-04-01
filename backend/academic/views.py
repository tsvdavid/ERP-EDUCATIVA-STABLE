from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Course, Subject, Enrollment, Grade, Attendance, EvaluationCategory, AcademicYear, AcademicPeriod, ClassSchedule
from .serializers import (
    CourseSerializer, 
    SubjectSerializer, 
    EnrollmentSerializer, 
    GradeSerializer, 
    AttendanceSerializer,
    EvaluationCategorySerializer,
    AcademicYearSerializer,
    AcademicPeriodSerializer,
    ClassScheduleSerializer
)
from users.permissions import IsAdminOrLocalAdminUser, IsRectorUser, IsTeacherUser, IsAdminUser
from rest_framework.decorators import action
from django.db.models import Count, Case, When, Q
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
            return [permissions.IsAuthenticated(), (IsAdminOrLocalAdminUser | IsRectorUser)()]
        return [permissions.IsAuthenticated()]

class AcademicPeriodViewSet(viewsets.ModelViewSet):
    queryset = AcademicPeriod.objects.all()
    serializer_class = AcademicPeriodSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), (IsAdminOrLocalAdminUser | IsRectorUser)()]
        return [permissions.IsAuthenticated()]

class CourseViewSet(viewsets.ModelViewSet):

    queryset = Course.objects.all().select_related('institution')
    serializer_class = CourseSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), (IsAdminOrLocalAdminUser | IsRectorUser)()]
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

    @action(detail=False, methods=['get'], url_path='excellence-ranking')
    def excellence_ranking(self, request):
        """
        Ranking of students with highest averages across the institution or filtered by course/level.
        """
        user = self.request.user
        queryset = self.get_queryset() # Respects institution and year filters
        
        level = request.query_params.get('level')
        course_id = request.query_params.get('course_id')
        year_id = request.query_params.get('academic_year_id')
        
        if year_id:
            try:
                ay = AcademicYear.objects.get(pk=year_id)
                queryset = queryset.filter(course__year=ay.year)
            except (AcademicYear.DoesNotExist, ValueError):
                pass
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        if level:
            queryset = queryset.filter(course__level=level)
            
        from typing import List, Dict, Any
        rankings: List[Dict[str, Any]] = []
        for enrollment in queryset:
            summary = enrollment.calculate_averages()
            if not summary:
                continue
                
            # Global Average (mean of all subjects' finals)
            final_scores = [data['final'] for data in summary.values() if data['final'] is not None]
            if not final_scores:
                continue
            
            avg = round(float(sum(final_scores) / len(final_scores)), 2)
            rankings.append({
                'student_id': enrollment.student.id,
                'student_name': f"{enrollment.student.first_name} {enrollment.student.last_name}",
                'course_name': f"{enrollment.course.name} {enrollment.course.parallel}",
                'level': enrollment.course.level,
                'average': avg
            })
            
        # Sort by average descending
        rankings = sorted(rankings, key=lambda x: x['average'], reverse=True)
        return Response(list(rankings)[:20]) # Top 20 for abanderados/escoltas

    @action(detail=False, methods=['get'], url_path='institution-stats')
    def institution_stats(self, request):
        """
        Aggregated demographic and disciplinary stats for the entire institution.
        """
        user = self.request.user
        inst_id = user.institution_id
        if not inst_id:
             inst_id = request.headers.get('X-Institution-ID')
             
        if not inst_id:
             return Response({"error": "No institution context found"}, status=400)
             
        # 1. Demographics (Students & Teachers)
        from users.models import User as CustomUser
        base_users = CustomUser.objects.filter(institution_id=inst_id)
        
        demographics = {
            'students': {
                'M': base_users.filter(role='STUDENT', gender='M').count(),
                'F': base_users.filter(role='STUDENT', gender='F').count(),
                'total': base_users.filter(role='STUDENT').count()
            },
            'teachers': {
                'M': base_users.filter(role='TEACHER', gender='M').count(),
                'F': base_users.filter(role='TEACHER', gender='F').count(),
                'total': base_users.filter(role='TEACHER').count()
            }
        }
        
        # 2. Disciplinary Summary
        from .models import Observation
        year_id = request.query_params.get('academic_year_id')
        course_id = request.query_params.get('course_id')
        
        obs_filter = Q(student__institution_id=inst_id)
        if year_id:
            # Observation doesn't have course/year directly, but we can filter via enrollment in that year
            obs_filter &= Q(student__enrollments__course__academic_year_id=year_id)
        if course_id:
            obs_filter &= Q(student__enrollments__course_id=course_id)
            
        observations = Observation.objects.filter(obs_filter).distinct()
        discipline = {
            'behavioral': observations.filter(type='BEHAVIORAL').count(),
            'academic': observations.filter(type='ACADEMIC').count(),
            'positive': observations.filter(type='POSITIVE').count(),
            'critical_high': observations.filter(criticality='HIGH').count()
        }
        
        # 3. Attendance Global
        from .models import Attendance
        att_filter = Q(enrollment__course__institution_id=inst_id)
        if year_id:
            att_filter &= Q(enrollment__course__academic_year_id=year_id)
        if course_id:
            att_filter &= Q(enrollment__course_id=course_id)
            
        attendance = Attendance.objects.filter(att_filter)
        att_summary = {
            'present': attendance.filter(status='PRESENT').count(),
            'absent': attendance.filter(status='ABSENT').count(),
            'late': attendance.filter(status='LATE').count(),
            'excused': attendance.filter(status='EXCUSED').count()
        }
        
        return Response({
            'demographics': demographics,
            'discipline': discipline,
            'attendance': att_summary
        })



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
            # Enrich summary with qualitative data
            subjects_data = [] # For graph
            scores_data = []   # For graph
            recommendations = [] # For PDF logic

            for subject_id, data in summary.items():
                data['qualitative'] = get_qualitative_score(data['final'])
                subjects_data.append(data['name'])
                scores_data.append(data['final'])
                
                # Parse final score to add recommendations
                if data['final'] is not None:
                    try:
                        score_val = float(data['final'])
                        if score_val >= 9.0:
                            recommendations.append({'subject': data['name'], 'type': 'success', 'message': '¡Excelente trabajo! Continúa reforzando estas habilidades.'})
                        elif score_val >= 7.0:
                            recommendations.append({'subject': data['name'], 'type': 'warning', 'message': 'Buen desempeño, esfuérzate un poco más para dominar los temas.'})
                        else:
                            recommendations.append({'subject': data['name'], 'type': 'danger', 'message': 'Alerta: Necesitas refuerzo académico. Busca apoyo con tu docente.'})
                    except Exception:
                        pass
            
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
            
            # --- ATTENDANCE SUMMARY ---
            attendance_records = enrollment.attendance_records.all()
            total_classes = attendance_records.count()
            attendance_summary = {
                'total_classes': total_classes, 'present': 0, 'absent': 0,
                'late': 0, 'excused': 0, 'percentage': 100.0
            }
            if total_classes > 0:
                p = attendance_records.filter(status='PRESENT').count()
                a = attendance_records.filter(status='ABSENT').count()
                l = attendance_records.filter(status='LATE').count()
                e = attendance_records.filter(status='EXCUSED').count()
                attended = p + l + e
                attendance_summary.update({
                    'present': p, 'absent': a, 'late': l, 'excused': e,
                    'percentage': round((attended / total_classes) * 100, 2)
                })

            # Prepare Context
            # Prepare Context
            context = {
                'enrollment': enrollment,
                'summary': summary,
                'institution': enrollment.course.institution,
                'logo_path': None,
                'chart_image': image_base64,
                'recommendations': recommendations,
                'attendance_summary': attendance_summary,
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

    @action(detail=False, methods=['get'], url_path='course-stats')
    def course_stats(self, request):
        """
        Endpoint to provide statistical data for grades in a course/subject.
        """
        course_id = request.query_params.get('course_id')
        subject_id = request.query_params.get('subject_id')
        
        if not course_id:
            return Response({"error": "course_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get the enrollments to calculate real averages
        enrollments = Enrollment.objects.filter(course_id=course_id)
        if not enrollments.exists():
            return Response({"error": "No hay matrículas en el curso"}, status=status.HTTP_404_NOT_FOUND)

        # Trimester breakdown and Distrubtion
        summary_results = []
        distribution = { "DA": 0, "AA": 0, "PA": 0, "NA": 0 }
        risk_students = []

        from decimal import Decimal
        trim_averages = {1: [], 2: [], 3: []}
        
        for e in enrollments:
            avgs = e.calculate_averages()
            
            # If subject_id is provided, limit to that subject
            if subject_id:
                if int(subject_id) in avgs:
                    subj_avg = avgs[int(subject_id)]
                else:
                    continue
            else:
                # Use global average of all subjects for this student
                if len(avgs) > 0:
                    total_final = sum(data['final'] for data in avgs.values()) / len(avgs)
                    subj_avg = {'final': total_final, 't1': 0, 't2': 0, 't3': 0}
                    # Approximate trimesters
                    for t in [1, 2, 3]:
                        t_vals = [data.get(f't{t}', 0) for data in avgs.values()]
                        subj_avg[f't{t}'] = sum(t_vals) / len(t_vals) if len(t_vals) > 0 else 0
                else:
                    continue
            
            final_score = subj_avg['final']
            # Distribute
            if final_score >= 9: distribution["DA"] += 1
            elif final_score >= 7: distribution["AA"] += 1
            elif final_score >= 4: distribution["PA"] += 1
            else: distribution["NA"] += 1
            
            # Risk
            if final_score < 7:
                risk_students.append({
                    "student_name": f"{e.student.first_name} {e.student.last_name}",
                    "score": round(float(final_score), 2),
                    "id": e.student.id
                })
                
            # Trimester arrays
            trim_averages[1].append(subj_avg.get('t1', 0))
            trim_averages[2].append(subj_avg.get('t2', 0))
            trim_averages[3].append(subj_avg.get('t3', 0))

        # Calculate averages for trimesters across course
        def avg_list(lst):
            actuals = [x for x in lst if x > 0]
            if not actuals: return 0
            return round(float(sum(actuals) / len(actuals)), 2)

        course_average = avg_list([subj_avg['final'] for subj_avg in [e.calculate_averages().get(int(subject_id) if subject_id else next(iter(e.calculate_averages())), {'final':0}) for e in enrollments] if 'final' in subj_avg])

        trimesters_chart = [
            {"name": "Tri 1", "promedio": avg_list(trim_averages[1])},
            {"name": "Tri 2", "promedio": avg_list(trim_averages[2])},
            {"name": "Tri 3", "promedio": avg_list(trim_averages[3])},
            {"name": "Final", "promedio": course_average},
        ]

        return Response({
            "course_average": course_average,
            "distribution": [
                {"name": "DA (9-10)", "value": distribution["DA"], "fill": "#10b981"},
                {"name": "AA (7-8.9)", "value": distribution["AA"], "fill": "#3b82f6"},
                {"name": "PA (4-6.9)", "value": distribution["PA"], "fill": "#f59e0b"},
                {"name": "NA (0-3.9)", "value": distribution["NA"], "fill": "#ef4444"},
            ],
            "trimesters": trimesters_chart,
            "risk_students": sorted(risk_students, key=lambda x: x['score'])
        })

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

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({"error": "course_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        enrollments = Enrollment.objects.filter(course_id=course_id).count()
        
        # Base filter
        att_filter = Attendance.objects.filter(enrollment__course_id=course_id)
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            att_filter = att_filter.filter(date__gte=start_date)
        if end_date:
            att_filter = att_filter.filter(date__lte=end_date)
            
        total_records = att_filter.count()
        present_count = att_filter.filter(status='PRESENT').count()
        absent_count = att_filter.filter(status='ABSENT').count()
        late_count = att_filter.filter(status='LATE').count()
        excused_count = att_filter.filter(status='EXCUSED').count()
        
        # Calculate percentages
        def get_pct(count):
            return round((count / total_records * 100), 2) if total_records > 0 else 0
            
        return Response({
            "total_students": enrollments,
            "total_records": total_records,
            "series": [
                {"name": "Presentes", "value": present_count, "fill": "#10b981"},
                {"name": "Atrasos", "value": late_count, "fill": "#f59e0b"},
                {"name": "Justificados", "value": excused_count, "fill": "#3b82f6"},
                {"name": "Ausencias", "value": absent_count, "fill": "#ef4444"},
            ],
            "global_attendance_pct": get_pct(present_count + late_count + excused_count)
        })

class ClassScheduleViewSet(viewsets.ModelViewSet):
    queryset = ClassSchedule.objects.all()
    serializer_class = ClassScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ClassSchedule.objects.all()
        user = self.request.user
        
        if user.role == 'STUDENT':
            queryset = queryset.filter(subject__course__enrollments__student=user).distinct()
        elif user.role == 'PARENT':
            student_id = self.request.query_params.get('student_id', None)
            if student_id:
                # Validar que el student_id pertenezca a los hijos del padre
                queryset = queryset.filter(
                    subject__course__enrollments__student_id=student_id, 
                    subject__course__enrollments__student__in=user.children.all()
                ).distinct()
            else:
                queryset = queryset.filter(subject__course__enrollments__student__in=user.children.all()).distinct()
        
        course_id = self.request.query_params.get('course', None)
        if course_id:
            queryset = queryset.filter(subject__course_id=course_id)
        
        return queryset

