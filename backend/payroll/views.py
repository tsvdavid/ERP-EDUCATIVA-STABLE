from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from users.tenant_mixins import InstitutionFilterMixin
from core.tenancy.viewsets import BaseTenantViewSet
from .models import (
    Employee,
    Contract,
    WorkShift,
    Department,
    Position,
    Attendance,
    PayrollPeriod,
    PayrollRoll,
)
from .serializers import (
    EmployeeSerializer,
    ContractSerializer,
    WorkShiftSerializer,
    DepartmentSerializer,
    PositionSerializer,
    AttendanceSerializer,
    PayrollPeriodSerializer,
    PayrollRollSerializer,
)
from .services import PayrollService


class EmployeeViewSet(InstitutionFilterMixin, BaseTenantViewSet):
    queryset = Employee.objects.unscoped()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = "institution"


class ContractViewSet(InstitutionFilterMixin, BaseTenantViewSet):
    queryset = Contract.objects.unscoped()
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = "institution"


class WorkShiftViewSet(InstitutionFilterMixin, BaseTenantViewSet):
    queryset = WorkShift.objects.unscoped()
    serializer_class = WorkShiftSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = "institution"


class AttendanceViewSet(InstitutionFilterMixin, BaseTenantViewSet):
    queryset = Attendance.objects.unscoped()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = "institution"


class PayrollPeriodViewSet(InstitutionFilterMixin, BaseTenantViewSet):
    queryset = PayrollPeriod.objects.unscoped()
    serializer_class = PayrollPeriodSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = "institution"

    def get_queryset(self):
        return super().get_queryset().order_by("-year", "-month")

    @action(detail=False, methods=["post"])
    def generate_nomina(self, request):
        year = int(request.data.get("year"))
        month = int(request.data.get("month"))
        try:
            period = PayrollService.generate_payroll_period(
                request.tenant, year, month, request.user
            )
            return Response(
                PayrollPeriodSerializer(period).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        period = self.get_object()
        try:
            entry = PayrollService.approve_and_post_accounting(period, request.user)
            return Response(
                {
                    "status": "APPROVED",
                    "journal_entry_id": entry.id,
                    "message": "Nómina aprobada y contabilidad generada.",
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def rolls(self, request, pk=None):
        period = self.get_object()
        rolls = period.rolls.all().prefetch_related("details")
        return Response(PayrollRollSerializer(rolls, many=True).data)


class PayrollRollViewSet(InstitutionFilterMixin, viewsets.ReadOnlyModelViewSet):
    queryset = PayrollRoll.objects.unscoped()
    serializer_class = PayrollRollSerializer
    tenant_field = "institution"

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        roll = self.get_object()
        from django.http import HttpResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from io import BytesIO

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, roll.institution.name)
        p.setFont("Helvetica", 12)
        p.drawString(
            50,
            height - 70,
            f"Rol de Pagos: {roll.period.month}/{roll.period.year}",
        )

        # Employee Info
        p.line(50, height - 80, width - 50, height - 80)
        p.drawString(
            50,
            height - 100,
            f"Empleado: {roll.employee.user.get_full_name()}",
        )
        p.drawString(50, height - 115, f"Cédula: {roll.employee.identification}")
        p.drawString(
            50,
            height - 130,
            f"Cargo: {roll.contract.position.name}",
        )
        p.line(50, height - 140, width - 50, height - 140)

        # Body
        y = height - 170
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Concepto")
        p.drawString(450, y, "Valor")
        p.setFont("Helvetica", 10)
        y -= 20
        for item in roll.details.all():
            p.drawString(50, y, item.name)
            p.drawString(450, y, f"$ {item.amount}")
            y -= 15

        # Footer
        p.line(50, y - 10, width - 50, y - 10)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y - 30, "NETO A RECIBIR:")
        p.drawString(450, y - 30, f"$ {roll.net_to_pay}")

        p.showPage()
        p.save()

        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="rol_{roll.employee.identification}.pdf"'
        )
        response.write(pdf)
        return response


class DepartmentViewSet(InstitutionFilterMixin, BaseTenantViewSet):
    queryset = Department.objects.unscoped()
    serializer_class = DepartmentSerializer
    tenant_field = "institution"


class PositionViewSet(InstitutionFilterMixin, BaseTenantViewSet):
    queryset = Position.objects.unscoped()
    serializer_class = PositionSerializer
    tenant_field = "institution"
