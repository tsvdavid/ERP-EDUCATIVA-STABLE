from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    MedicalRecord, MedicalVisit, DeceRecord, DeceVisit,
    BehaviorRecord, BehaviorCase, CaseFollowUp,
    StudentRiskProfile, AlertRule
)
from .serializers import (
    MedicalRecordSerializer, MedicalVisitSerializer,
    DeceRecordSerializer, DeceVisitSerializer,
    BehaviorRecordSerializer, BehaviorCaseSerializer,
    BehaviorCaseSummarySerializer, CaseFollowUpSerializer,
    StudentRiskProfileSerializer, AlertRuleSerializer
)

STAFF_ROLES = ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'DECE', 'MEDICO', 'TEACHER']
DECE_ROLES  = ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'DECE']
ADMIN_ROLES = ['ADMIN', 'LOCAL_ADMIN', 'RECTOR']


# ─── FICHAS PERMANENTES ────────────────────────────────────────────────────────

class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'STUDENT':
            return MedicalRecord.objects.filter(student=user)
        if user.role == 'PARENT':
            return MedicalRecord.objects.filter(student__in=user.children.all())
        return MedicalRecord.objects.all()


class MedicalVisitViewSet(viewsets.ModelViewSet):
    queryset = MedicalVisit.objects.all()
    serializer_class = MedicalVisitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = MedicalVisit.objects.all()
        if user.role == 'STUDENT':
            return qs.filter(student=user)
        if user.role == 'PARENT':
            return qs.filter(student__in=user.children.all())
        student_id = self.request.query_params.get('student')
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user)


class DeceRecordViewSet(viewsets.ModelViewSet):
    queryset = DeceRecord.objects.all()
    serializer_class = DeceRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'STUDENT':
            return DeceRecord.objects.filter(student=user)
        if user.role == 'PARENT':
            return DeceRecord.objects.filter(student__in=user.children.all())
        return DeceRecord.objects.all()


class DeceVisitViewSet(viewsets.ModelViewSet):
    queryset = DeceVisit.objects.all()
    serializer_class = DeceVisitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = DeceVisit.objects.all()
        if user.role == 'STUDENT':
            return qs.filter(student=user)
        if user.role == 'PARENT':
            return qs.filter(student__in=user.children.all())
        student_id = self.request.query_params.get('student')
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(counselor=self.request.user)


# ─── REGISTROS CONDUCTUALES ───────────────────────────────────────────────────

class BehaviorRecordViewSet(viewsets.ModelViewSet):
    queryset = BehaviorRecord.objects.select_related('student', 'created_by', 'subject', 'course', 'academic_year')
    serializer_class = BehaviorRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = BehaviorRecord.objects.select_related('student', 'created_by', 'subject', 'course', 'academic_year')

        if user.role == 'STUDENT':
            qs = qs.filter(student=user)
        elif user.role == 'PARENT':
            qs = qs.filter(student__in=user.children.all())

        # Filtros opcionales
        student_id = self.request.query_params.get('student')
        year_id    = self.request.query_params.get('academic_year')
        rec_type   = self.request.query_params.get('record_type')
        course_id  = self.request.query_params.get('course')
        subject_id = self.request.query_params.get('subject')
        date_str   = self.request.query_params.get('date')

        if student_id:
            qs = qs.filter(student_id=student_id)
        if year_id:
            qs = qs.filter(academic_year_id=year_id)
        if rec_type:
            qs = qs.filter(record_type=rec_type)
        if course_id:
            qs = qs.filter(course_id=course_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if date_str:
            qs = qs.filter(date=date_str)

        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        record = serializer.save(created_by=self.request.user)
        # Disparar motor de reglas
        try:
            user = self.request.user
            institution = getattr(user, 'institution', None)
            if institution:
                from .utils import evaluate_alert_rules
                evaluate_alert_rules(record.student, institution, record.academic_year)
        except Exception:
            pass

    @action(detail=False, methods=['post'], url_path='quick-create')
    def quick_create(self, request):
        """Registro rápido desde modal en Asistencia/Calificaciones."""
        data = request.data.copy()
        # Si no viene academic_year, usar el año activo
        if not data.get('academic_year'):
            try:
                from academic.models import AcademicYear
                year = AcademicYear.objects.filter(is_active=True).first()
                if year:
                    data['academic_year'] = year.id
            except Exception:
                pass

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            record = serializer.save(created_by=request.user)
            try:
                institution = getattr(request.user, 'institution', None)
                if institution:
                    from .utils import evaluate_alert_rules
                    cases = evaluate_alert_rules(record.student, institution, record.academic_year)
                    return Response({
                        **serializer.data,
                        'alert_triggered': len(cases) > 0,
                        'cases_created': len(cases),
                    }, status=status.HTTP_201_CREATED)
            except Exception:
                pass
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='by-student')
    def by_student(self, request):
        """Registros de un estudiante filtrado por año lectivo."""
        student_id = request.query_params.get('student')
        year_id    = request.query_params.get('academic_year')
        if not student_id:
            return Response({'error': 'Se requiere student'}, status=400)
        qs = self.get_queryset().filter(student_id=student_id)
        if year_id:
            qs = qs.filter(academic_year_id=year_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ─── CASOS CONDUCTUALES ───────────────────────────────────────────────────────

class BehaviorCaseViewSet(viewsets.ModelViewSet):
    queryset = BehaviorCase.objects.select_related('student', 'assigned_to', 'created_by', 'academic_year')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return BehaviorCaseSummarySerializer
        return BehaviorCaseSerializer

    def get_queryset(self):
        user = self.request.user
        qs = BehaviorCase.objects.select_related('student', 'assigned_to', 'created_by', 'academic_year')

        # Filtrar por área según rol
        if user.role == 'DECE':
            qs = qs.filter(area='DECE')
        elif user.role == 'MEDICO':
            qs = qs.filter(area='MEDICAL')
        elif user.role not in ADMIN_ROLES:
            return qs.none()

        # Filtros opcionales
        params = self.request.query_params
        if params.get('student'):
            qs = qs.filter(student_id=params['student'])
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        if params.get('priority'):
            qs = qs.filter(priority=params['priority'])
        if params.get('area'):
            qs = qs.filter(area=params['area'])
        if params.get('academic_year'):
            qs = qs.filter(academic_year_id=params['academic_year'])

        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def derive(self, request, pk=None):
        """Derivar caso a otra área (DECE ↔ Dispensario Médico)."""
        case = self.get_object()
        new_area = request.data.get('area')
        reason   = request.data.get('reason', '')

        if new_area not in ['DECE', 'MEDICAL']:
            return Response({'error': 'Área inválida. Use DECE o MEDICAL.'}, status=400)
        if new_area == case.area:
            return Response({'error': 'El caso ya está en esa área.'}, status=400)

        old_area = case.area
        # Crear caso derivado
        new_case = BehaviorCase.objects.create(
            student=case.student,
            academic_year=case.academic_year,
            area=new_area,
            status='OPEN',
            priority=case.priority,
            title=f"[Derivado] {case.title}",
            description=f"Derivado desde {old_area}.\n\nMotivo: {reason}\n\n{case.description}",
            created_by=request.user,
            parent_case=case,
            derived_from_area=old_area,
        )
        new_case.behavior_records.set(case.behavior_records.all())

        # Agregar seguimiento de derivación al caso original
        CaseFollowUp.objects.create(
            case=case,
            follow_up_type='REFERRAL',
            content=f"Caso derivado a {new_area}. Motivo: {reason}",
            created_by=request.user,
            is_confidential=False,
        )
        case.status = 'IN_PROGRESS'
        case.save()

        serializer = BehaviorCaseSummarySerializer(new_case)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Cerrar un caso con resumen."""
        case = self.get_object()
        summary = request.data.get('summary', '')

        if case.status == 'CLOSED':
            return Response({'error': 'El caso ya está cerrado.'}, status=400)

        case.status = 'CLOSED'
        case.closed_at = timezone.now()
        case.save()

        if summary:
            CaseFollowUp.objects.create(
                case=case,
                follow_up_type='NOTE',
                content=f"CIERRE DE CASO:\n{summary}",
                created_by=request.user,
                is_confidential=False,
            )

        # Actualizar perfil de riesgo
        try:
            from .utils import calculate_risk_profile
            calculate_risk_profile(case.student, case.academic_year)
        except Exception:
            pass

        serializer = BehaviorCaseSerializer(case, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reabrir un caso cerrado."""
        case = self.get_object()
        if case.status != 'CLOSED':
            return Response({'error': 'Solo se pueden reabrir casos cerrados.'}, status=400)
        case.status = 'IN_PROGRESS'
        case.closed_at = None
        case.save()
        serializer = BehaviorCaseSerializer(case, context={'request': request})
        return Response(serializer.data)


# ─── SEGUIMIENTOS ─────────────────────────────────────────────────────────────

class CaseFollowUpViewSet(viewsets.ModelViewSet):
    queryset = CaseFollowUp.objects.select_related('case', 'created_by')
    serializer_class = CaseFollowUpSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = CaseFollowUp.objects.select_related('case', 'created_by')
        case_id = self.request.query_params.get('case')
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        follow_up = serializer.save(created_by=self.request.user)
        # Actualizar estado del caso a IN_PROGRESS si estaba OPEN
        case = follow_up.case
        if case.status == 'OPEN':
            case.status = 'IN_PROGRESS'
            case.save()


# ─── PERFILES DE RIESGO ───────────────────────────────────────────────────────

class StudentRiskProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StudentRiskProfile.objects.select_related('student', 'academic_year')
    serializer_class = StudentRiskProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role not in DECE_ROLES + ['MEDICO']:
            return StudentRiskProfile.objects.none()
        qs = StudentRiskProfile.objects.select_related('student', 'academic_year')
        params = self.request.query_params
        if params.get('academic_year'):
            qs = qs.filter(academic_year_id=params['academic_year'])
        if params.get('risk_level'):
            qs = qs.filter(overall_risk=params['risk_level'])
        if params.get('student'):
            qs = qs.filter(student_id=params['student'])
        return qs

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Estadísticas globales del semáforo para el dashboard DECE."""
        year_id = request.query_params.get('academic_year')
        qs = StudentRiskProfile.objects.all()
        if year_id:
            qs = qs.filter(academic_year_id=year_id)

        totals = qs.aggregate(
            green=Count('id', filter=Q(overall_risk='GREEN')),
            yellow=Count('id', filter=Q(overall_risk='YELLOW')),
            red=Count('id', filter=Q(overall_risk='RED')),
        )

        # Casos activos
        case_qs = BehaviorCase.objects.filter(status__in=['OPEN', 'IN_PROGRESS'])
        if year_id:
            case_qs = case_qs.filter(academic_year_id=year_id)
        cases_by_area = case_qs.values('area').annotate(count=Count('id'))

        # Registros recientes (últimos 7 días)
        from django.utils import timezone
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        recent_records = BehaviorRecord.objects.filter(created_at__gte=week_ago)
        if year_id:
            recent_records = recent_records.filter(academic_year_id=year_id)
        records_by_type = recent_records.values('record_type').annotate(count=Count('id'))

        return Response({
            'risk_summary': totals,
            'total_students': sum(totals.values()),
            'cases_by_area': list(cases_by_area),
            'records_last_7d': list(records_by_type),
            'open_cases': case_qs.filter(status='OPEN').count(),
            'in_progress_cases': case_qs.filter(status='IN_PROGRESS').count(),
        })

    @action(detail=False, methods=['post'], url_path='recalculate-all')
    def recalculate_all(self, request):
        """Recalcular semáforo de todos los estudiantes del año activo."""
        if request.user.role not in ADMIN_ROLES + ['DECE']:
            return Response({'error': 'Sin permisos.'}, status=403)
        try:
            from academic.models import AcademicYear
            from users.models import User
            from .utils import calculate_risk_profile
            year_id = request.data.get('academic_year')
            if year_id:
                year = AcademicYear.objects.get(id=year_id)
            else:
                year = AcademicYear.objects.filter(is_active=True).first()
            if not year:
                return Response({'error': 'No hay año lectivo activo.'}, status=400)

            students = User.objects.filter(role='STUDENT')
            count = 0
            for student in students:
                calculate_risk_profile(student, year)
                count += 1
            return Response({'message': f'Perfiles recalculados: {count} estudiantes.'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


# ─── REGLAS DE ALERTA ─────────────────────────────────────────────────────────

class AlertRuleViewSet(viewsets.ModelViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role not in ADMIN_ROLES + ['DECE']:
            return AlertRule.objects.none()
        qs = AlertRule.objects.all()
        institution = getattr(user, 'institution', None)
        if institution:
            qs = qs.filter(institution=institution)
        return qs

    def perform_create(self, serializer):
        institution = getattr(self.request.user, 'institution', None)
        if institution:
            serializer.save(institution=institution)
        else:
            serializer.save()
