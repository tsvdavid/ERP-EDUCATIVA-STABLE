from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import PayrollPeriod, PayrollRoll, PayrollItem, Contract, Attendance, Employee
from accounting.models import JournalEntry, JournalItem, AccountingConfig
from accounting.signals import get_configured_account
import calendar

class PayrollService:
    @staticmethod
    def generate_payroll_period(institution, year, month, user):
        """
        Genera la nómina para todos los empleados activos de la institución.
        """
        from accounting.models import MonthlyClose
        with transaction.atomic():
            # 1. Validar Cierre Mensual
            if MonthlyClose.objects.filter(institution=institution, year=year, month=month, is_closed=True).exists():
                raise ValueError(f"El periodo {month}/{year} está cerrado contablemente. No se puede generar nómina.")

            # 2. Bloqueo de concurrencia
            period, created = PayrollPeriod.objects.select_for_update().get_or_create(
                institution=institution,
                year=year,
                month=month,
                defaults={'state': 'DRAFT'}
            )
            
            if not created and period.state != 'DRAFT':
                raise ValueError("No se puede regenerar una nómina que ya ha sido aprobada o pagada.")

            # Limpiar roles anteriores si existen para regenerar
            period.rolls.all().delete()

            contracts = Contract.objects.filter(
                institution=institution,
                is_active=True,
                start_date__lte=timezone.datetime(year, month, calendar.monthrange(year, month)[1]).date()
            ).select_related('employee', 'employee__user')

            for contract in contracts:
                PayrollService.calculate_employee_roll(period, contract)

            return period

    @staticmethod
    def calculate_employee_roll(period, contract):
        employee = contract.employee
        base_salary = contract.base_salary
        
        # Calcular Horas Extra (Placeholder simplificado para este hardening)
        # En producción real esto sumaría Attendance.overtime_hours
        overtime_hours = Attendance.objects.filter(
            employee=employee,
            date__year=period.year,
            date__month=period.month
        ).aggregate(models.Sum('overtime_hours'))['overtime_hours__sum'] or Decimal('0.00')
        
        hourly_rate = base_salary / Decimal('240') # 240 horas laborales al mes (Ecuador standard)
        overtime_amount = (overtime_hours * hourly_rate * Decimal('1.5')).quantize(Decimal('0.01')) # 50% extra surcharge
        
        # Ingresos Totales
        gross_earnings = base_salary + overtime_amount
        
        # Descuentos (IESS Personal 9.45% en Ecuador)
        iess_personal = (gross_earnings * Decimal('0.0945')).quantize(Decimal('0.01'))
        
        net_to_pay = gross_earnings - iess_personal
        
        # Provisiones Legales Ecuador (Acumulación)
        provision_13th = (gross_earnings / Decimal('12')).quantize(Decimal('0.01'))
        sbu = Decimal('460.00') # SBU 2026 Ecuador
        provision_14th = (sbu / Decimal('12')).quantize(Decimal('0.01'))
        provision_reserve = (gross_earnings * Decimal('0.0833')).quantize(Decimal('0.01'))
        
        iess_patronal = (gross_earnings * Decimal('0.1215')).quantize(Decimal('0.01'))
        company_cost = gross_earnings + iess_patronal + provision_13th + provision_14th + provision_reserve

        roll = PayrollRoll.objects.create(
            institution=period.institution,
            period=period,
            employee=employee,
            contract=contract,
            base_salary=base_salary,
            overtime_total=overtime_amount,
            iess_personal=iess_personal,
            iess_patronal=iess_patronal,
            provision_13th=provision_13th,
            provision_14th=provision_14th,
            provision_reserve_funds=provision_reserve,
            net_to_pay=net_to_pay,
            company_cost=company_cost
        )

        # Crear items de detalle
        PayrollItem.objects.create(roll=roll, institution=period.institution, item_type='EARNING', name='Sueldo Base', amount=base_salary)
        if overtime_amount > 0:
            PayrollItem.objects.create(roll=roll, institution=period.institution, item_type='EARNING', name='Horas Extra', amount=overtime_amount)
        
        PayrollItem.objects.create(roll=roll, institution=period.institution, item_type='DEDUCTION', name='Aporte IESS Personal (9.45%)', amount=iess_personal)
        
        # Informativos de provisión (para el rol individual)
        PayrollItem.objects.create(roll=roll, institution=period.institution, item_type='EARNING', name='Prov. Décimo Tercero (Inf.)', amount=provision_13th)
        PayrollItem.objects.create(roll=roll, institution=period.institution, item_type='EARNING', name='Prov. Décimo Cuarto (Inf.)', amount=provision_14th)

        return roll

    @staticmethod
    def approve_and_post_accounting(period, user):
        """
        Aprueba la nómina y genera el asiento contable automático.
        """
        if period.state != 'DRAFT':
            raise ValueError("Solo se pueden aprobar nóminas en estado Borrador.")

        from accounting.models import MonthlyClose
        with transaction.atomic():
            # 1. Validar Cierre Mensual
            if MonthlyClose.objects.filter(institution=period.institution, year=period.year, month=period.month, is_closed=True).exists():
                raise ValueError("No se puede aprobar nómina en un periodo cerrado contablemente.")

            # 2. Totales de la nómina
            totals = PayrollRoll.objects.filter(period=period).aggregate(
                total_salaries=models.Sum('base_salary') + models.Sum('overtime_total'),
                total_iess_personal=models.Sum('iess_personal'),
                total_net=models.Sum('net_to_pay'),
                total_cost=models.Sum('company_cost'),
                total_benefits=models.Sum('provision_13th') + models.Sum('provision_14th') + models.Sum('provision_reserve_funds')
            )
            
            iess_patronal_total = totals['total_cost'] - totals['total_salaries']
            iess_total_payable = totals['total_iess_personal'] + iess_patronal_total

            # 2. Generar Asiento Contable
            entry = JournalEntry.objects.create(
                institution=period.institution,
                date=timezone.datetime(period.year, period.month, calendar.monthrange(period.year, period.month)[1]).date(),
                description=f"Asiento de Nómina Mensual - {calendar.month_name[period.month]} {period.year}",
                reference=f"NOM-{period.year}-{period.month}",
                state='POSTED',
                created_by=user
            )

            # --- DEBITOS (GASTOS) ---
            # Gasto Sueldos
            salary_expense_acc = get_configured_account(period.institution, 'EXPENSE_SALARIES', '5.1')
            JournalItem.objects.create(
                institution=period.institution,
                journal_entry=entry,
                account=salary_expense_acc,
                description="Gasto de Sueldos y Salarios",
                debit=totals['total_salaries'],
                credit=0
            )
            
            # Gasto Aporte Patronal
            patronal_expense_acc = get_configured_account(period.institution, 'EXPENSE_SOCIAL_SECURITY', '5.1')
            JournalItem.objects.create(
                institution=period.institution,
                journal_entry=entry,
                account=patronal_expense_acc,
                description="Gasto Aporte Patronal IESS",
                debit=iess_patronal_total,
                credit=0
            )

            # Gasto Beneficios Sociales (Provisiones)
            benefits_expense_acc = get_configured_account(period.institution, 'EXPENSE_BENEFITS', '5.1')
            JournalItem.objects.create(
                institution=period.institution,
                journal_entry=entry,
                account=benefits_expense_acc,
                description="Gasto Provisión de Beneficios Sociales (Décimos + Fondos)",
                debit=totals['total_benefits'],
                credit=0
            )

            # --- CREDITOS (PASIVOS) ---
            # Sueldos por Pagar
            salaries_payable_acc = get_configured_account(period.institution, 'LIABILITY_SALARIES_PAYABLE', '2.1')
            JournalItem.objects.create(
                institution=period.institution,
                journal_entry=entry,
                account=salaries_payable_acc,
                description="Sueldos y Salarios por Pagar",
                debit=0,
                credit=totals['total_net']
            )
            
            # IESS por Pagar
            iess_payable_acc = get_configured_account(period.institution, 'LIABILITY_IESS_PAYABLE', '2.1')
            JournalItem.objects.create(
                institution=period.institution,
                journal_entry=entry,
                account=iess_payable_acc,
                description="Aportes IESS por Pagar (Personal + Patronal)",
                debit=0,
                credit=iess_total_payable
            )

            # Beneficios Sociales por Pagar (Provisiones)
            benefits_payable_acc = get_configured_account(period.institution, 'LIABILITY_BENEFITS_PAYABLE', '2.1')
            JournalItem.objects.create(
                institution=period.institution,
                journal_entry=entry,
                account=benefits_payable_acc,
                description="Provisión de Beneficios Sociales por Pagar (Décimos + Fondos)",
                debit=0,
                credit=totals['total_benefits']
            )

            if not entry.is_balanced:
                raise ValueError(f"El asiento contable de nómina está descuadrado: D:{entry.total_debit} C:{entry.total_credit}")

            # 3. Actualizar Estado
            period.state = 'APPROVED'
            period.approved_at = timezone.now()
            period.approved_by = user
            period.save()

            return entry

from django.db import models # Added missing import
