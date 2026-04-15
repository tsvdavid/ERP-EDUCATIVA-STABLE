import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from users.models import User, Institution
from accounting.models import FiscalYear, Account, JournalEntry, JournalItem, AccountingConfig
from treasury.models import PaymentMethod, PaymentConcept, StudentAccount, Invoice, InvoiceDetail, Payment, Charge
from purchases.models import Supplier, PurchaseInvoice, PurchaseItem

class Command(BaseCommand):
    help = 'Populates the database with comprehensive Accounting data (NIIF Ecuador)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando población de datos contables COMPLETA...'))

        with transaction.atomic():
            # 0. Get Institution
            institution = Institution.objects.first()
            if not institution:
                self.stdout.write(self.style.ERROR('No existe institución. Ejecute populate_test_data primero.'))
                return

            # Clear existing accounting data to avoid duplicates/conflicts if re-running
            self.stdout.write("Limpiando datos contables anteriores...")
            
            # 1. Delete transactions first (Dependent objects)
            from purchases.models import PurchaseCreditNote, PurchaseDebitNote
            PurchaseCreditNote.objects.filter(institution=institution).delete()
            PurchaseDebitNote.objects.filter(institution=institution).delete()
            
            PurchaseInvoice.objects.filter(institution=institution).delete() # Cascades to PurchaseItem
            Invoice.objects.filter(institution=institution).delete() # Cascades to InvoiceDetail, Payment
            Charge.objects.filter(institution=institution).delete()
            JournalEntry.objects.filter(institution=institution).delete() # Cascades to JournalItem
            
            # 2. Delete Catalogs (now that they are not referenced)
            AccountingConfig.objects.filter(institution=institution).delete()
            PaymentConcept.objects.filter(institution=institution).delete()
            Supplier.objects.filter(institution=institution).delete()
            Account.objects.filter(institution=institution).delete()

            # 1. Fiscal Year
            fiscal_year, created = FiscalYear.objects.get_or_create(
                institution=institution, year=2026,
                defaults={'is_closed': False}
            )
            self.stdout.write(self.style.SUCCESS(f'Año Fiscal 2026 activo.'))

            # 2. Comprehensive Chart of Accounts (Plan de Cuentas NIIF)
            self.stdout.write("Generando Plan de Cuentas NIIF...")

            # Structure: (Code, Name, Type, ParentCode)
            # ParentCode=None means Root
            accounts_data = [
                # 1. ACTIVO
                ('1', 'ACTIVO', 'ASSET', None),
                ('1.1', 'ACTIVO CORRIENTE', 'ASSET', '1'),
                
                ('1.1.01', 'Efectivo y Equivalentes al Efectivo', 'ASSET', '1.1'),
                ('1.1.01.01', 'Caja General', 'ASSET', '1.1.01'),
                ('1.1.01.02', 'Caja Chica', 'ASSET', '1.1.01'),
                ('1.1.01.05', 'Instituciones Financieras Públicas', 'ASSET', '1.1.01'),
                ('1.1.01.10', 'Instituciones Financieras Privadas', 'ASSET', '1.1.01'),
                ('1.1.01.10.01', 'Banco Pichincha Cta. Cte.', 'ASSET', '1.1.01.10'),
                ('1.1.01.10.02', 'Banco Guayaquil Cta. Ahorros', 'ASSET', '1.1.01.10'),

                ('1.1.02', 'Inversiones Financieras', 'ASSET', '1.1'),
                ('1.1.02.01', 'Inversiones a Corto Plazo', 'ASSET', '1.1.02'),

                ('1.1.03', 'Cuentas y Documentos por Cobrar', 'ASSET', '1.1'),
                ('1.1.03.01', 'Clientes Relacionados', 'ASSET', '1.1.03'),
                ('1.1.03.02', 'Clientes No Relacionados (Estudiantes)', 'ASSET', '1.1.03'), 
                ('1.1.03.03', 'Otras Cuentas por Cobrar', 'ASSET', '1.1.03'),
                ('1.1.03.03.01', 'Anticipos a Empleados', 'ASSET', '1.1.03.03'),
                ('1.1.03.03.02', 'Préstamos a Empleados', 'ASSET', '1.1.03.03'),

                ('1.1.04', 'Inventarios', 'ASSET', '1.1'),
                ('1.1.04.01', 'Mercaderías en Bodega', 'ASSET', '1.1.04'),
                ('1.1.04.01.01', 'Inventario de Uniformes', 'ASSET', '1.1.04.01'),
                ('1.1.04.01.02', 'Inventario de Textos y Útiles', 'ASSET', '1.1.04.01'),
                ('1.1.04.02', 'Suministros y Materiales', 'ASSET', '1.1.04'),
                
                ('1.1.05', 'Servicios y Otros Pagos Anticipados', 'ASSET', '1.1'),
                ('1.1.05.01', 'Seguros Prepagados', 'ASSET', '1.1.05'),
                ('1.1.05.02', 'Arriendos Prepagados', 'ASSET', '1.1.05'),

                ('1.1.06', 'Activos por Impuestos Corrientes', 'ASSET', '1.1'),
                ('1.1.06.01', 'Crédito Tributario a Favor (IVA)', 'ASSET', '1.1.06'),
                ('1.1.06.02', 'Crédito Tributario a Favor (Renta)', 'ASSET', '1.1.06'),
                ('1.1.06.03', 'IVA Compras (Transitorio)', 'ASSET', '1.1.06'),

                ('1.2', 'ACTIVO NO CORRIENTE', 'ASSET', '1'),
                ('1.2.01', 'Propiedad, Planta y Equipo', 'ASSET', '1.2'),
                ('1.2.01.01', 'Terrenos', 'ASSET', '1.2.01'),
                ('1.2.01.02', 'Edificios', 'ASSET', '1.2.01'),
                ('1.2.01.03', 'Muebles y Enseres', 'ASSET', '1.2.01'),
                ('1.2.01.04', 'Maquinaria y Equipo', 'ASSET', '1.2.01'),
                ('1.2.01.05', 'Equipos de Computación', 'ASSET', '1.2.01'),
                ('1.2.01.06', 'Vehículos', 'ASSET', '1.2.01'),
                
                ('1.2.02', 'Depreciación Acumulada PPE (-)', 'ASSET', '1.2'),
                ('1.2.02.01', 'Dep. Acum. Edificios', 'ASSET', '1.2.02'),
                ('1.2.02.02', 'Dep. Acum. Muebles y Enseres', 'ASSET', '1.2.02'),
                ('1.2.02.03', 'Dep. Acum. Equipos de Computación', 'ASSET', '1.2.02'),

                # 2. PASIVO
                ('2', 'PASIVO', 'LIABILITY', None),
                ('2.1', 'PASIVO CORRIENTE', 'LIABILITY', '2'),
                
                ('2.1.01', 'Cuentas y Documentos por Pagar', 'LIABILITY', '2.1'),
                ('2.1.01.01', 'Proveedores Locales', 'LIABILITY', '2.1.01'),
                ('2.1.01.02', 'Proveedores del Exterior', 'LIABILITY', '2.1.01'),
                
                ('2.1.02', 'Obligaciones con la Administración Tributaria', 'LIABILITY', '2.1'),
                ('2.1.02.01', 'IVA Cobrado (En Ventas)', 'LIABILITY', '2.1.02'),
                ('2.1.02.02', 'Retención en la Fuente IR por Pagar', 'LIABILITY', '2.1.02'),
                ('2.1.02.03', 'Retención IVA por Pagar', 'LIABILITY', '2.1.02'),
                ('2.1.02.04', 'Impuesto a la Renta por Pagar', 'LIABILITY', '2.1.02'),

                ('2.1.03', 'Obligaciones con el IESS', 'LIABILITY', '2.1'),
                ('2.1.03.01', 'Aporte Individual por Pagar', 'LIABILITY', '2.1.03'),
                ('2.1.03.02', 'Aporte Patronal por Pagar', 'LIABILITY', '2.1.03'),
                ('2.1.03.03', 'Préstamos Quirografarios/Hipotecarios', 'LIABILITY', '2.1.03'),

                ('2.1.04', 'Obligaciones Laborales', 'LIABILITY', '2.1'),
                ('2.1.04.01', 'Sueldos por Pagar', 'LIABILITY', '2.1.04'),
                ('2.1.04.02', 'Décimo Tercer Sueldo', 'LIABILITY', '2.1.04'),
                ('2.1.04.03', 'Décimo Cuarto Sueldo', 'LIABILITY', '2.1.04'),
                ('2.1.04.04', 'Vacaciones por Pagar', 'LIABILITY', '2.1.04'),
                ('2.1.04.05', 'Participación Trabajadores por Pagar', 'LIABILITY', '2.1.04'),

                ('2.2', 'PASIVO NO CORRIENTE', 'LIABILITY', '2'),
                ('2.2.01', 'Préstamos Bancarios Largo Plazo', 'LIABILITY', '2.2'),
                ('2.2.02', 'Jubilación Patronal', 'LIABILITY', '2.2'),

                # 3. PATRIMONIO
                ('3', 'PATRIMONIO', 'EQUITY', None),
                ('3.1', 'PATRIMONIO NETO', 'EQUITY', '3'),
                ('3.1.01', 'Capital Social', 'EQUITY', '3.1'),
                ('3.1.02', 'Reservas', 'EQUITY', '3.1'),
                ('3.1.02.01', 'Reserva Legal', 'EQUITY', '3.1.02'),
                ('3.1.03', 'Resultados Acumulados', 'EQUITY', '3.1'),
                ('3.1.03.01', 'Utilidad de Ejercicios Anteriores', 'EQUITY', '3.1.03'),
                ('3.1.03.02', 'Pérdida de Ejercicios Anteriores', 'EQUITY', '3.1.03'),
                ('3.1.04', 'Resultado del Ejercicio', 'EQUITY', '3.1'),
                ('3.1.04.01', 'Utilidad del Ejercicio', 'EQUITY', '3.1.04'),
                ('3.1.04.02', 'Pérdida del Ejercicio', 'EQUITY', '3.1.04'),

                # 4. INGRESOS
                ('4', 'INGRESOS', 'INCOME', None),
                ('4.1', 'INGRESOS OPERACIONALES', 'INCOME', '4'),
                
                ('4.1.01', 'Prestación de Servicios Educativos', 'INCOME', '4.1'),
                ('4.1.01.01', 'Ingresos por Matrículas', 'INCOME', '4.1.01'),
                ('4.1.01.02', 'Ingresos por Pensiones', 'INCOME', '4.1.01'),
                ('4.1.01.03', 'Ingresos por Derechos de Exámenes', 'INCOME', '4.1.01'),
                ('4.1.01.04', 'Plataformas Digitales', 'INCOME', '4.1.01'),

                ('4.1.02', 'Venta de Bienes', 'INCOME', '4.1'),
                ('4.1.02.01', 'Venta de Uniformes', 'INCOME', '4.1.02'),
                ('4.1.02.02', 'Venta de Textos y Útiles', 'INCOME', '4.1.02'),
                ('4.1.02.03', 'Bar Escolar', 'INCOME', '4.1.02'),

                ('4.2', 'OTROS INGRESOS', 'INCOME', '4'),
                ('4.2.01', 'Ingresos Financieros (Intereses)', 'INCOME', '4.2'),
                ('4.2.02', 'Otros Ingresos No Operacionales', 'INCOME', '4.2'),

                # 5. GASTOS Y COSTOS
                ('5', 'COSTOS Y GASTOS', 'EXPENSE', None),
                
                ('5.1', 'COSTO DE VENTAS', 'EXPENSE', '5'),
                ('5.1.01', 'Costo de Ventas Bienes', 'EXPENSE', '5.1'),
                ('5.1.01.01', 'Costo Uniformes', 'EXPENSE', '5.1.01'),
                ('5.1.01.02', 'Costo Libros', 'EXPENSE', '5.1.01'),

                ('5.2', 'GASTOS ADMINISTRATIVOS', 'EXPENSE', '5'),
                
                ('5.2.01', 'Gastos de Personal', 'EXPENSE', '5.2'),
                ('5.2.01.01', 'Sueldos y Salarios', 'EXPENSE', '5.2.01'),
                ('5.2.01.02', 'Horas Extras', 'EXPENSE', '5.2.01'),
                ('5.2.01.03', 'Aporte Patronal IESS', 'EXPENSE', '5.2.01'),
                ('5.2.01.04', 'Fondo de Reserva', 'EXPENSE', '5.2.01'),
                ('5.2.01.05', 'Decimotercer Sueldo', 'EXPENSE', '5.2.01'),
                ('5.2.01.06', 'Decimocuarto Sueldo', 'EXPENSE', '5.2.01'),
                ('5.2.01.07', 'Vacaciones', 'EXPENSE', '5.2.01'),

                ('5.2.02', 'Honorarios Profesionales', 'EXPENSE', '5.2'),
                ('5.2.02.01', 'Asesoría Legal', 'EXPENSE', '5.2.02'),
                ('5.2.02.02', 'Asesoría Contable', 'EXPENSE', '5.2.02'),
                ('5.2.02.03', 'Soporte Técnico', 'EXPENSE', '5.2.02'),

                ('5.2.03', 'Servicios Básicos', 'EXPENSE', '5.2'),
                ('5.2.03.01', 'Agua Potable', 'EXPENSE', '5.2.03'),
                ('5.2.03.02', 'Energía Eléctrica', 'EXPENSE', '5.2.03'),
                ('5.2.03.03', 'Teléfono y Telecomunicaciones', 'EXPENSE', '5.2.03'),
                ('5.2.03.04', 'Internet', 'EXPENSE', '5.2.03'),

                ('5.2.04', 'Mantenimiento y Reparaciones', 'EXPENSE', '5.2'),
                ('5.2.04.01', 'Mantinimiento Edificios', 'EXPENSE', '5.2.04'),
                ('5.2.04.02', 'Mantenimiento Equipos', 'EXPENSE', '5.2.04'),
                ('5.2.04.03', 'Limpieza y Aseo', 'EXPENSE', '5.2.04'),

                ('5.2.05', 'Suministros y Materiales', 'EXPENSE', '5.2'),
                ('5.2.05.01', 'Suministros de Oficina', 'EXPENSE', '5.2.05'),
                ('5.2.05.02', 'Material Didáctico', 'EXPENSE', '5.2.05'),

                ('5.2.06', 'Impuestos, Contribuciones y Seguros', 'EXPENSE', '5.2'),
                ('5.2.06.01', 'Impuestos Municipales', 'EXPENSE', '5.2.06'),
                ('5.2.06.02', 'Contribuciones Supercias', 'EXPENSE', '5.2.06'),
                ('5.2.06.03', 'Seguros', 'EXPENSE', '5.2.06'),

                ('5.2.07', 'Depreciaciones y Amortizaciones', 'EXPENSE', '5.2'),
                ('5.2.07.01', 'Depreciación Edificios', 'EXPENSE', '5.2.07'),
                ('5.2.07.02', 'Depreciación Muebles y Enseres', 'EXPENSE', '5.2.07'),
                ('5.2.07.03', 'Depreciación Equipos de Computación', 'EXPENSE', '5.2.07'),

                ('5.3', 'GASTOS FINANCIEROS', 'EXPENSE', '5'),
                ('5.3.01', 'Intereses Bancarios', 'EXPENSE', '5.3'),
                ('5.3.02', 'Comisiones Bancarias', 'EXPENSE', '5.3'),
            ]

            acc_cache = {} # code -> object

            # Create Root accounts first, then children
            # Sorting by code length ensures parents are created before children
            accounts_data.sort(key=lambda x: len(x[0]))

            for code, name, type, parent_code in accounts_data:
                parent = acc_cache.get(parent_code) if parent_code else None
                acc, _ = Account.objects.get_or_create(
                    institution=institution, code=code,
                    defaults={'name': name, 'account_type': type, 'parent': parent}
                )
                acc_cache[code] = acc
                # self.stdout.write(f'Cuenta creada: {code} - {name}')

            self.stdout.write(self.style.SUCCESS(f'Plan de Cuentas generado ({len(accounts_data)} cuentas).'))

            # 3. Configure Default Accounts (AccountingConfig)
            # Map system keys to specific accounts from our new chart
            Mapping = [
                ('ASSET_CASH', acc_cache['1.1.01.01']),
                ('ASSET_BANK', acc_cache['1.1.01.10.01']), # Pichincha
                ('ASSET_CXC', acc_cache['1.1.03.02']), # Estudiantes
                ('LIABILITY_IVA', acc_cache['2.1.02.01']), # IVA Cobrado
                ('INCOME_SERVICES', acc_cache['4.1.01.02']), # Pensiones
                ('LIABILITY_SUPPLIERS', acc_cache['2.1.01.01']), # Proveedores Locales
                ('ASSET_TAX_CREDIT', acc_cache['1.1.06.03']), # IVA Compras
            ]
            for key, account in Mapping:
                AccountingConfig.objects.update_or_create(
                    institution=institution, key=key, defaults={'account': account}
                )
            
            self.stdout.write("Configuración contable base establecida.")

            # 4. Initial Balance (Asiento de Apertura)
            admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
            
            entry = JournalEntry.objects.create(
                institution=institution,
                date=date(2026, 1, 1),
                description="Asiento de Apertura 2026 (Situación Inicial)",
                state='POSTED',
                created_by=admin_user,
                posted_at=date(2026, 1, 1)
            )
            
            # DEBE (Activos)
            # Caja: 2.000
            # Bancos: 15.000
            # Muebles: 12.000
            # Equipos: 8.000
            # Edificios: 120.000
            # Terreno: 50.000
            JournalItem.objects.create(journal_entry=entry, account=acc_cache['1.1.01.01'], debit=2000)
            JournalItem.objects.create(journal_entry=entry, account=acc_cache['1.1.01.10.01'], debit=15000) 
            JournalItem.objects.create(journal_entry=entry, account=acc_cache['1.2.01.03'], debit=12000)
            JournalItem.objects.create(journal_entry=entry, account=acc_cache['1.2.01.05'], debit=8000)
            JournalItem.objects.create(journal_entry=entry, account=acc_cache['1.2.01.02'], debit=120000)
            JournalItem.objects.create(journal_entry=entry, account=acc_cache['1.2.01.01'], debit=50000)

            # HABER (Pasivos + Patrimonio)
            # Préstamo Bancario LP: 60.000
            # Capital Social: 147.000 (Diferencia)
            JournalItem.objects.create(journal_entry=entry, account=acc_cache['2.2.01'], credit=60000)
            JournalItem.objects.create(journal_entry=entry, account=acc_cache['3.1.01'], credit=147000)
            
            self.stdout.write(self.style.SUCCESS('Asiento de apertura creado y balanceado ($207,000).'))

            # 5. Payment Methods & Concepts (Tesorería)
            efectivo, _ = PaymentMethod.objects.get_or_create(institution=institution, code='EFECTIVO', defaults={'name': 'Efectivo'})
            transferencia, _ = PaymentMethod.objects.get_or_create(institution=institution, code='TRANSFERENCIA', defaults={'name': 'Transferencia Bancaria'})

            concepts_data = [
                ('Matrícula 2026', Decimal('120.00'), Decimal('0.00')),
                ('Pensión Abril 2026', Decimal('180.00'), Decimal('0.00')),
                ('Pensión Mayo 2026', Decimal('180.00'), Decimal('0.00')),
                ('Kit Uniforme Diario', Decimal('65.00'), Decimal('0.15')),
                ('Kit Uniforme Deportivo', Decimal('75.00'), Decimal('0.15')),
                ('Agenda Escolar', Decimal('15.00'), Decimal('0.15')),
                ('Plataforma Digital Anual', Decimal('40.00'), Decimal('0.15')),
            ]
            
            concepts = {}
            for name, price, iva in concepts_data:
                concepts[name], _ = PaymentConcept.objects.get_or_create(
                    institution=institution, name=name,
                    defaults={'price': price, 'iva_rate': iva, 'is_active': True}
                )

            # 6. Suppliers (Proveedores REALES con validación)
            suppliers_data = [
                ('1791234567001', 'PAPELERIA NACIONAL S.A.', 'Super Paco', 'Av. 10 de Agosto', True), # Contribuyente Especial
                ('1798765432001', 'CONFECCIONES TEXTILES ECUADOR', 'Textiles El Rayo', 'Calle Los Álamos', False),
                ('1792468135001', 'PROVEEDORA DE INTERNET NETLIFE', 'Netlife', 'Av. Eloy Alfaro', True),
                ('1791357924001', 'LIMPIEZA PROFESIONAL CIA LTDA', 'CleanMaster', 'Sector El Inca', False),
                ('0102030405001', 'JUAN MECANICO', 'Taller Juanito', 'La Kennedy', False),
            ]
            
            suppliers = []
            for ruc, legal, trade, addr, special in suppliers_data:
                sup, s_created = Supplier.objects.get_or_create(
                    institution=institution, tax_id=ruc,
                    defaults={
                        'legal_name': legal, 'trade_name': trade, 'address': addr, 
                        'email': f"facturacion@{trade.lower().replace(' ', '')}.com.ec",
                        'phone': '022999999',
                        'is_special_taxpayer': special,
                        'tax_id_type': 'RUC'
                    }
                )
                suppliers.append(sup)

            self.stdout.write(self.style.SUCCESS(f'{len(suppliers)} Proveedores validados creados.'))

            # 7. Purchases (Compras Variadas)
            
            # A. Compra de Suministros (Gasto) - CleanMaster
            if not PurchaseInvoice.objects.filter(document_number='001-002-000000555').exists():
                inv = PurchaseInvoice.objects.create(
                    institution=institution, supplier=suppliers[3],
                    document_number='001-002-000000555',
                    issue_date=date(2026, 2, 10),
                    subtotal_15=300.00, iva=45.00, total=345.00,
                    status='VALIDATED', created_by=admin_user,
                    payment_method='20'
                )
                PurchaseItem.objects.create(
                    invoice=inv, description='Servicio de Limpieza y Mantenimiento Febrero',
                    quantity=1, unit_price=300, subtotal=300, tax_rate=15,
                    expense_account=acc_cache['5.2.04.03'] # Limpieza y Aseo
                )
            
            # B. Compra de Inventario (Activo) - Textiles El Rayo
            if not PurchaseInvoice.objects.filter(document_number='001-001-000012345').exists():
                inv = PurchaseInvoice.objects.create(
                    institution=institution, supplier=suppliers[1],
                    document_number='001-001-000012345',
                    issue_date=date(2026, 3, 5),
                    subtotal_15=2000.00, iva=300.00, total=2300.00,
                    status='VALIDATED', created_by=admin_user
                )
                PurchaseItem.objects.create(
                    invoice=inv, description='Camisetas Polo Institucionales',
                    quantity=100, unit_price=10, subtotal=1000, tax_rate=15,
                    expense_account=acc_cache['1.1.04.01.01'] # Inv Uniformes
                )
                PurchaseItem.objects.create(
                    invoice=inv, description='Chompas Deportivas',
                    quantity=50, unit_price=20, subtotal=1000, tax_rate=15,
                    expense_account=acc_cache['1.1.04.01.01'] # Inv Uniformes
                )

            # C. Compra Activo Fijo (Computadoras) - Super Paco
            if not PurchaseInvoice.objects.filter(document_number='002-001-000008888').exists():
                inv = PurchaseInvoice.objects.create(
                    institution=institution, supplier=suppliers[0],
                    document_number='002-001-000008888',
                    issue_date=date(2026, 1, 15),
                    subtotal_15=4000.00, iva=600.00, total=4600.00,
                    status='VALIDATED', created_by=admin_user
                )
                PurchaseItem.objects.create(
                    invoice=inv, description='Laptops Dell Vostro (Administración)',
                    quantity=5, unit_price=800, subtotal=4000, tax_rate=15,
                    expense_account=acc_cache['1.2.01.05'] # Equipos de Computación
                )

            self.stdout.write(self.style.SUCCESS('Compras variadas generadas (Gasto, Inventario, Activo Fijo).'))

            # 8. Student Invoices (Facturación Masiva)
            students = User.objects.filter(role='STUDENT', institution=institution)
            if students.exists():
                self.stdout.write("Generando facturación a estudiantes...")
                
                count = 0
                for i, student in enumerate(students):
                    if i >= 15: break # Limit
                    
                    # Ensure student account
                    StudentAccount.objects.get_or_create(student=student, institution=institution)
                    
                    # 1. Factura Matrícula (PAGADA)
                    inv_num = f'001-001-{str(5000 + i).zfill(9)}'
                    if not Invoice.objects.filter(number=inv_num).exists():
                        inv = Invoice.objects.create(
                            institution=institution, student=student, number=inv_num,
                            client_name=f"{student.first_name} {student.last_name}",
                            client_ruc="9999999999999", client_address="Quito, Ecuador",
                            status='ISSUED', created_by=admin_user, payment_method=transferencia,
                            subtotal_0=120.00, total=120.00,
                            issue_date=date(2026, 4, 1) # Backdate
                        )
                        InvoiceDetail.objects.create(
                            invoice=inv, concept=concepts['Matrícula 2026'], quantity=1, unit_price=120.00, subtotal=120.00
                        )
                        Payment.objects.create(invoice=inv, amount_paid=120.00, verified=True)
                    
                    # 2. Factura Uniformes (PAGADA)
                    inv_num_uni = f'001-001-{str(6000 + i).zfill(9)}'
                    if not Invoice.objects.filter(number=inv_num_uni).exists():
                         inv = Invoice.objects.create(
                            institution=institution, student=student, number=inv_num_uni,
                            client_name=f"{student.first_name} {student.last_name}",
                            client_ruc="9999999999999",
                            status='ISSUED', created_by=admin_user, payment_method=efectivo,
                            subtotal_15=65.00, iva_total=9.75, total=74.75,
                            issue_date=date(2026, 4, 5)
                        )
                         InvoiceDetail.objects.create(
                            invoice=inv, concept=concepts['Kit Uniforme Diario'], quantity=1, unit_price=65.00, subtotal=65.00
                        )
                         Payment.objects.create(invoice=inv, amount_paid=74.75, verified=True)
                    
                    count += 1
                
                self.stdout.write(self.style.SUCCESS(f'Facturación generada para {count} estudiantes.'))
        
        self.stdout.write(self.style.SUCCESS('¡Población de datos contables FINALIZADA CORRECTAMENTE!'))
