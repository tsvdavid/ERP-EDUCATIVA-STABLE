import io
import pandas as pd
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import LMSCourse, LMSEnrollment, Assignment, AssignmentSubmission
from academic.models import Enrollment as AcademicEnrollment, AcademicYear
from django.db.models import Count, Q

class InstructorExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        export_format = request.query_params.get('format', 'excel')
        course_id = request.query_params.get('course_id')
        user = request.user
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': 'No institution context found'}, status=status.HTTP_400_BAD_REQUEST)
        
        submissions = AssignmentSubmission.objects.filter(
            assignment__module__course__instructor=user,
            assignment__module__course__institution=tenant,
        ).select_related(
            'student', 'assignment', 'assignment__module', 'assignment__module__course'
        )
        if course_id:
            submissions = submissions.filter(assignment__module__course_id=course_id)
            
        data = []
        for sub in submissions:
            data.append({
                'Alumno': sub.student.get_full_name(),
                'Email': sub.student.email,
                'Curso': sub.assignment.module.course.title,
                'Tarea': sub.assignment.title,
                'Fecha Envío': sub.submitted_at.strftime('%Y-%m-%d %H:%M') if sub.submitted_at else 'N/A',
                'Calificación': sub.score if sub.score is not None else 'Pendiente',
                'Puntaje Máximo': sub.assignment.max_score
            })
            
        if export_format == 'excel':
            df = pd.DataFrame(data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Entregas')
            output.seek(0)
            
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=reporte_panel_docente.xlsx'
            return response

        elif export_format == 'csv':
            df = pd.DataFrame(data)
            output = io.StringIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            
            response = HttpResponse(
                output.getvalue(),
                content_type='text/csv'
            )
            response['Content-Disposition'] = 'attachment; filename=reporte_panel_docente.csv'
            return response
            
        elif export_format == 'pdf':
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer)
            p.setFont("Helvetica-Bold", 16)
            p.drawString(50, 800, "Eduka360 - Reporte de Entregas")
            p.setFont("Helvetica", 10)
            p.drawString(50, 780, f"Docente: {user.get_full_name()}")
            p.drawString(50, 765, f"Fecha: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
            
            y = 730
            p.setFont("Helvetica-Bold", 9)
            p.drawString(50, y, "ALUMNO")
            p.drawString(200, y, "CURSO")
            p.drawString(350, y, "TAREA")
            p.drawString(500, y, "NOTA")
            p.line(50, y-5, 550, y-5)
            
            y -= 25
            p.setFont("Helvetica", 8)
            for item in data[:30]: # Limit for demo
                if y < 50:
                    p.showPage()
                    y = 800
                p.drawString(50, y, item['Alumno'][:30])
                p.drawString(200, y, item['Curso'][:30])
                p.drawString(350, y, item['Tarea'][:30])
                p.drawString(500, y, str(item['Calificación']))
                y -= 15
                
            p.showPage()
            p.save()
            buffer.seek(0)
            
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename=reporte_panel_docente.pdf'
            return response
            
        return Response({'error': 'Formato no soportado'}, status=status.HTTP_400_BAD_REQUEST)

class InstructorDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': 'No institution context found'}, status=400)
        is_admin = hasattr(user, 'role') and str(user.role).upper() == 'ADMIN' or user.is_staff or user.is_superuser
        
        # Estadísticas básicas con logs de depuración
        try:
            print("--- INICIANDO CAPTURA DE ESTADÍSTICAS DASHBOARD ---")
            if is_admin:
                print("Modo: ADMIN")
                total_courses = LMSCourse.objects.filter(institution=tenant).count()
                print(f"Cursos LMS: {total_courses}")
                total_enrolled = LMSEnrollment.objects.filter(course__institution=tenant).values('user').distinct().count()
                print(f"Inscritos LMS: {total_enrolled}")
                active_students = AcademicEnrollment.objects.filter(
                    student__is_active=True,
                    student__institution=tenant,
                ).values('student').distinct().count()
                print(f"Alumnos Activos Académicos: {active_students}")
                pending_assignments = AssignmentSubmission.objects.filter(
                    score__isnull=True,
                    assignment__module__course__institution=tenant,
                ).count()
                print(f"Tareas Pendientes: {pending_assignments}")
                
                active_year = AcademicYear.objects.filter(institution=tenant, is_active=True).first()
                if not active_year:
                    active_year = AcademicYear.objects.filter(institution=tenant).order_by('-year').first()
                print(f"Año Lectivo Detectado: {active_year}")
            else:
                print(f"Modo: DOCENTE ({user.username})")
                instructor_courses = LMSCourse.objects.filter(instructor=user, institution=tenant)
                total_courses = instructor_courses.count()
                print(f"Mis Cursos LMS: {total_courses}")
                
                enrollments = LMSEnrollment.objects.filter(course__in=instructor_courses)
                total_enrolled = enrollments.values('user').distinct().count()
                print(f"Mis Inscritos LMS: {total_enrolled}")
                
                # Para docentes, filtramos alumnos activos por las materias que dictan
                active_students = AcademicEnrollment.objects.filter(course__subjects__teacher=user, student__is_active=True).values('student').distinct().count()
                print(f"Mis Alumnos Activos Académicos: {active_students}")
                
                pending_assignments = AssignmentSubmission.objects.filter(
                    assignment__module__course__instructor=user,
                    assignment__module__course__institution=tenant,
                    score__isnull=True
                ).count()
                print(f"Mis Tareas Pendientes: {pending_assignments}")
                
                active_year = AcademicYear.objects.filter(institution=tenant, is_active=True).first()
                print(f"Año Lectivo Docente: {active_year}")

            return Response({
                'total_courses': total_courses,
                'total_students': total_enrolled,
                'active_students': active_students,
                'pending_assignments': pending_assignments,
                'active_year_name': active_year.name if active_year else 'SISTEMA GLOBAL'
            })
        except Exception as e:
            import traceback
            print("!!! ERROR CRÍTICO EN DASHBOARD STATS !!!")
            print(traceback.format_exc())
            return Response({'error': str(e), 'traceback': traceback.format_exc()}, status=500)

class UnifiedSubmissionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': 'No institution context found'}, status=400)
        course_id = request.query_params.get('course_id')
        
        queryset = AssignmentSubmission.objects.filter(
            assignment__module__course__instructor=user,
            assignment__module__course__institution=tenant,
        ).select_related(
            'student', 'assignment', 'assignment__module', 'assignment__module__course'
        ).order_by('-submitted_at')
        
        if course_id:
            queryset = queryset.filter(assignment__module__course_id=course_id)
            
        data = []
        for sub in queryset:
            data.append({
                'id': sub.id,
                'student_name': sub.student.get_full_name(),
                'student_email': sub.student.email,
                'course_title': sub.assignment.module.course.title,
                'assignment_title': sub.assignment.title,
                'submitted_at': sub.submitted_at,
                'score': sub.score,
                'max_score': sub.assignment.max_score,
                'teacher_feedback': sub.teacher_feedback,
                'file': sub.file.url if sub.file else None
            })
            
        return Response(data)
