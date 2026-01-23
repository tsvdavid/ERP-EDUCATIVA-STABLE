from django.core.management.base import BaseCommand
from accounting.models import Account
from users.models import Institution

class Command(BaseCommand):
    help = 'Seeds Standard Ecuadorian Chart of Accounts'

    def handle(self, *args, **kwargs):
        # Default Institution (or iterate all)
        institutions = Institution.objects.all()
        if not institutions.exists():
            self.stdout.write(self.style.WARNING('No institutions found.'))
            return

        for inst in institutions:
            self.stdout.write(f'Seeding accounts for {inst.name}...')
            self.seed_accounts(inst)

    def seed_accounts(self, inst):
        # 1. ACTIVO
        activo, _ = Account.objects.get_or_create(code='1', defaults={'name': 'ACTIVO', 'account_type': 'ASSET', 'institution': inst})
        
        # 1.1 Activo Corriente
        a_corr, _ = Account.objects.get_or_create(code='1.1', defaults={'name': 'ACTIVO CORRIENTE', 'account_type': 'ASSET', 'parent': activo, 'institution': inst})
        
        # 1.1.01 Efectivo y Equivalentes
        efectivo, _ = Account.objects.get_or_create(code='1.1.01', defaults={'name': 'EFECTIVO Y EQUIVALENTES DE EFECTIVO', 'account_type': 'ASSET', 'parent': a_corr, 'institution': inst, 'tax_id': '101'})
        Account.objects.get_or_create(code='1.1.01.01', defaults={'name': 'Caja', 'account_type': 'ASSET', 'parent': efectivo, 'institution': inst})
        Account.objects.get_or_create(code='1.1.01.02', defaults={'name': 'Bancos', 'account_type': 'ASSET', 'parent': efectivo, 'institution': inst})
        
        # 1.1.02 Cuentas por Cobrar
        cxc, _ = Account.objects.get_or_create(code='1.1.02', defaults={'name': 'CUENTAS Y DOCUMENTOS POR COBRAR', 'account_type': 'ASSET', 'parent': a_corr, 'institution': inst})
        Account.objects.get_or_create(code='1.1.02.01', defaults={'name': 'Clientes', 'account_type': 'ASSET', 'parent': cxc, 'institution': inst})

        # 2. PASIVO
        pasivo, _ = Account.objects.get_or_create(code='2', defaults={'name': 'PASIVO', 'account_type': 'LIABILITY', 'institution': inst})
        
        p_corr, _ = Account.objects.get_or_create(code='2.1', defaults={'name': 'PASIVO CORRIENTE', 'account_type': 'LIABILITY', 'parent': pasivo, 'institution': inst})
        
        cxp, _ = Account.objects.get_or_create(code='2.1.01', defaults={'name': 'CUENTAS POR PAGAR', 'account_type': 'LIABILITY', 'parent': p_corr, 'institution': inst})
        Account.objects.get_or_create(code='2.1.01.01', defaults={'name': 'Proveedores', 'account_type': 'LIABILITY', 'parent': cxp, 'institution': inst})

        # 3. PATRIMONIO
        patrimonio, _ = Account.objects.get_or_create(code='3', defaults={'name': 'PATRIMONIO', 'account_type': 'EQUITY', 'institution': inst})
        Account.objects.get_or_create(code='3.1', defaults={'name': 'CAPITAL SOCIAL', 'account_type': 'EQUITY', 'parent': patrimonio, 'institution': inst})

        # 4. INGRESOS
        ingresos, _ = Account.objects.get_or_create(code='4', defaults={'name': 'INGRESOS', 'account_type': 'INCOME', 'institution': inst})
        v_ord, _ = Account.objects.get_or_create(code='4.1', defaults={'name': 'INGRESOS DE ACTIVIDADES ORDINARIAS', 'account_type': 'INCOME', 'parent': ingresos, 'institution': inst})
        Account.objects.get_or_create(code='4.1.01', defaults={'name': 'Venta de Bienes', 'account_type': 'INCOME', 'parent': v_ord, 'institution': inst})
        Account.objects.get_or_create(code='4.1.02', defaults={'name': 'Prestación de Servicios', 'account_type': 'INCOME', 'parent': v_ord, 'institution': inst})

        # 5. GASTOS
        gastos, _ = Account.objects.get_or_create(code='5', defaults={'name': 'GASTOS', 'account_type': 'EXPENSE', 'institution': inst})
        g_op, _ = Account.objects.get_or_create(code='5.1', defaults={'name': 'GASTOS OPERACIONALES', 'account_type': 'EXPENSE', 'parent': gastos, 'institution': inst})
        Account.objects.get_or_create(code='5.1.01', defaults={'name': 'Sueldos y Salarios', 'account_type': 'EXPENSE', 'parent': g_op, 'institution': inst})
        Account.objects.get_or_create(code='5.1.02', defaults={'name': 'Aportes a la Seguridad Social', 'account_type': 'EXPENSE', 'parent': g_op, 'institution': inst})


        self.stdout.write(self.style.SUCCESS(f'Successfully seeded accounts for {inst.name}'))
