from django.db import transaction
from django.utils import timezone
from django.core.management import call_command
from .models import Institution, User
from accounting.models import Account, AccountingConfig, FiscalYear
from treasury.models import PaymentMethod
from decimal import Decimal

class InstitutionBootstrapService:
    """
    Enterprise-grade Service to initialize new institutions.
    Handles Chart of Accounts, Configs, and Treasury defaults.
    """

    @staticmethod
    @transaction.atomic
    def bootstrap(institution):
        """
        Main entry point for bootstrapping an existing institution record.
        """
        if institution.setup_status == 'READY':
            return institution

        institution.setup_status = 'IN_PROGRESS'
        institution.save()

        from core.tenant_context import tenant_context

        def _create_fiscal_year():
            with tenant_context(institution.id):
                current_year = timezone.now().year
                FiscalYear.objects.get_or_create(
                    institution=institution,
                    year=current_year,
                    defaults={'is_closed': False}
                )

        def _create_accounts():
            with tenant_context(institution.id):
                accounts_data = [
                    ('1', 'ACTIVO', 'ASSET', None),
                    ('1.1', 'ACTIVO CORRIENTE', 'ASSET', '1'),
                    ('1.1.01', 'Efectivo y Equivalentes', 'ASSET', '1.1'),
                    ('1.1.01.01', 'Caja General', 'ASSET', '1.1.01'),
                    ('1.1.01.10', 'Bancos', 'ASSET', '1.1.01'),
                    ('1.1.01.10.01', 'Banco Pichincha', 'ASSET', '1.1.01.10'),
                    ('1.1.03', 'Cuentas por Cobrar', 'ASSET', '1.1'),
                    ('1.1.03.02', 'Cuentas por Cobrar Clientes', 'ASSET', '1.1.03'),
                    ('2', 'PASIVO', 'LIABILITY', None),
                    ('2.1', 'PASIVO CORRIENTE', 'LIABILITY', '2'),
                    ('2.1.02', 'Obligaciones Tributarias', 'LIABILITY', '2.1'),
                    ('2.1.02.01', 'IVA Cobrado', 'LIABILITY', '2.1.02'),
                    ('2.1.03', 'Obligaciones IESS', 'LIABILITY', '2.1'),
                    ('2.1.03.01', 'IESS por Pagar', 'LIABILITY', '2.1.03'),
                    ('2.1.04', 'Obligaciones Laborales', 'LIABILITY', '2.1'),
                    ('2.1.04.01', 'Sueldos por Pagar', 'LIABILITY', '2.1.04'),
                    ('3', 'PATRIMONIO', 'EQUITY', None),
                    ('3.1', 'PATRIMONIO NETO', 'EQUITY', '3'),
                    ('3.1.03', 'Resultados', 'EQUITY', '3.1'),
                    ('3.1.03.01', 'Utilidad de Ejercicios Anteriores', 'EQUITY', '3.1.03'),
                    ('4', 'INGRESOS', 'INCOME', None),
                    ('4.1', 'INGRESOS OPERACIONALES', 'INCOME', '4'),
                    ('4.1.01', 'Servicios Educativos', 'INCOME', '4.1'),
                    ('4.1.01.01', 'Matrículas', 'INCOME', '4.1.01'),
                    ('4.1.01.02', 'Pensiones', 'INCOME', '4.1.01'),
                    ('5', 'GASTOS', 'EXPENSE', None),
                    ('5.1', 'COSTOS', 'EXPENSE', '5'),
                    ('5.1.02', 'Costo de Ventas / Descuentos', 'EXPENSE', '5.1'),
                    ('5.2', 'GASTOS OPERATIVOS', 'EXPENSE', '5'),
                    ('5.2.01', 'Gastos de Personal', 'EXPENSE', '5.2'),
                    ('5.2.01.01', 'Sueldos y Salarios', 'EXPENSE', '5.2.01'),
                ]

                acc_cache = {}
                accounts_data.sort(key=lambda x: len(x[0]))
                
                for code, name, acc_type, parent_code in accounts_data:
                    parent = acc_cache.get(parent_code) if parent_code else None
                    acc, _ = Account.objects.get_or_create(
                        institution=institution,
                        code=code,
                        defaults={'name': name, 'account_type': acc_type, 'parent': parent}
                    )
                    acc_cache[code] = acc

                config_mapping = [
                    ('ASSET_CASH', '1.1.01.01'),
                    ('ASSET_BANK', '1.1.01.10.01'),
                    ('ASSET_CXC', '1.1.03.02'),
                    ('LIABILITY_IVA', '2.1.02.01'),
                    ('INCOME_SERVICES', '4.1.01.02'),
                    ('EXPENSE_DISCOUNTS', '5.1.02'),
                    ('EXPENSE_SALARIES', '5.2.01.01'),
                    ('LIABILITY_SALARIES_PAYABLE', '2.1.04.01'),
                    ('LIABILITY_IESS_PAYABLE', '2.1.03.01'),
                    ('EQUITY_RETAINED_EARNINGS', '3.1.03.01'),
                ]

                for key, code in config_mapping:
                    AccountingConfig.objects.update_or_create(
                        institution=institution,
                        key=key,
                        defaults={'account': acc_cache[code]}
                    )

        def _create_payment_methods():
            with tenant_context(institution.id):
                PaymentMethod.objects.get_or_create(
                    institution=institution,
                    code='EFECTIVO',
                    defaults={'name': 'Efectivo'}
                )
                PaymentMethod.objects.get_or_create(
                    institution=institution,
                    code='TRANSFERENCIA',
                    defaults={'name': 'Transferencia Bancaria'}
                )

        try:
            # Ejecutar cada grupo forzando su propio tenant_context
            _create_fiscal_year()
            _create_accounts()
            _create_payment_methods()

            institution.setup_status = 'READY_MINIMAL'
            institution.setup_completed_at = timezone.now()
            institution.setup_error = None
            institution.save()

            return institution

        except Exception as e:
            institution.setup_status = 'FAILED'
            institution.setup_error = str(e)
            institution.save()
            raise e

    @classmethod
    @transaction.atomic
    def create_and_bootstrap(cls, institution_data):
        """
        Creates a new institution and bootstraps it in a single transaction.
        If bootstrap fails, everything rolls back.
        """
        institution = Institution.objects.create(**institution_data)
        
        from core.tenant_context import tenant_context
        with tenant_context(institution.id):
            # Bloquear la fila explícitamente en la conexión actual
            locked_institution = Institution.objects.select_for_update().get(id=institution.id)
            return cls.bootstrap(locked_institution)
