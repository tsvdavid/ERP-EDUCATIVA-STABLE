from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Account, FiscalYear, MonthlyClose, JournalEntry, JournalItem, Bank, BankAccount, FixedAsset, Depreciation, AccountingConfig
from .serializers import (
    AccountSerializer, FiscalYearSerializer, JournalEntrySerializer, 
    BankSerializer, BankAccountSerializer, FixedAssetSerializer,
    AccountingConfigSerializer, MonthlyCloseSerializer
)
from decimal import Decimal
from django.utils import timezone
from users.tenant_mixins import InstitutionFilterMixin
from users.permissions import IsGlobalAdmin

class FiscalYearViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = FiscalYear.objects.all()
    serializer_class = FiscalYearSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = 'institution'

    def get_queryset(self):
        return super().get_queryset().order_by('-year')

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)

    @action(detail=True, methods=['post'])
    def close_year(self, request, pk=None):
        from decimal import Decimal
        from .models import JournalEntry, JournalItem, AccountingConfig
        from django.db.models import Sum
        import datetime

        fiscal_year = self.get_object()
        institution = request.user.institution

        if fiscal_year.is_closed:
            return Response({'error': 'El año fiscal ya está cerrado.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get Retained Earnings Account
        try:
            config = AccountingConfig.objects.get(institution=institution, key='EQUITY_RETAINED_EARNINGS')
            retained_earnings_account = config.account
        except AccountingConfig.DoesNotExist:
            return Response({'error': 'Debe configurar la cuenta de Resultados Acumulados en Configuraciones Contables antes de cerrar el año.'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate Income and Expenses
        start_date = datetime.date(fiscal_year.year, 1, 1)
        end_date = datetime.date(fiscal_year.year, 12, 31)

        items = JournalItem.objects.filter(
            account__institution=institution,
            journal_entry__state='POSTED',
            journal_entry__date__gte=start_date,
            journal_entry__date__lte=end_date
        )

        income_items = items.filter(account__account_type='INCOME')
        expense_items = items.filter(account__account_type='EXPENSE')

        income_balances = income_items.values('account').annotate(
            net=Sum('credit') - Sum('debit')
        ).filter(net__gt=0)

        expense_balances = expense_items.values('account').annotate(
            net=Sum('debit') - Sum('credit')
        ).filter(net__gt=0)
        
        total_income = sum(item['net'] for item in income_balances) if income_balances else Decimal('0.00')
        total_expense = sum(item['net'] for item in expense_balances) if expense_balances else Decimal('0.00')

        if total_income == Decimal('0.00') and total_expense == Decimal('0.00'):
            fiscal_year.is_closed = True
            fiscal_year.save()
            return Response({'status': 'ok', 'message': 'Año cerrado. No hubo ingresos ni egresos para generar un asiento.'})

        entry = JournalEntry.objects.create(
            institution=institution,
            date=end_date,
            description=f"Cierre del Ejercicio Fiscal {fiscal_year.year}",
            reference=f"CIERRE-{fiscal_year.year}",
            state='POSTED',
            created_by=request.user
        )

        for ib in income_balances:
            JournalItem.objects.create(
                journal_entry=entry,
                account_id=ib['account'],
                debit=ib['net'],
                credit=Decimal('0.00'),
                description="Cierre de cuenta de Ingreso"
            )

        for eb in expense_balances:
            JournalItem.objects.create(
                journal_entry=entry,
                account_id=eb['account'],
                debit=Decimal('0.00'),
                credit=eb['net'],
                description="Cierre de cuenta de Gasto"
            )

        net_income = total_income - total_expense

        if net_income > Decimal('0.00'):
            JournalItem.objects.create(
                journal_entry=entry,
                account=retained_earnings_account,
                debit=Decimal('0.00'),
                credit=net_income,
                description=f"Utilidad del Ejercicio {fiscal_year.year}"
            )
        elif net_income < Decimal('0.00'):
            JournalItem.objects.create(
                journal_entry=entry,
                account=retained_earnings_account,
                debit=abs(net_income),
                credit=Decimal('0.00'),
                description=f"Pérdida del Ejercicio {fiscal_year.year}"
            )

        if not entry.is_balanced:
            entry.delete()
            return Response({'error': 'Error de cuadre en el asiento de automático. Por favor contacte a soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        fiscal_year.is_closed = True
        fiscal_year.save()

        return Response({
            'status': 'ok', 
            'message': 'Año cerrado y asiento Cierre del Ejercicio generado exitosamente.',
            'journal_entry_id': entry.id
        })

class MonthlyCloseViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = MonthlyClose.objects.all()
    serializer_class = MonthlyCloseSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = 'institution'

    def perform_create(self, serializer):
        # Logic to ensure the month isn't already closed via POST
        month = serializer.validated_data.get('month')
        year = serializer.validated_data.get('year')
        
        if MonthlyClose.objects.filter(institution=self.request.user.institution, year=year, month=month, is_closed=True).exists():
             raise serializers.ValidationError("Este periodo ya se encuentra cerrado.")

        serializer.save(
            institution=self.request.user.institution,
            closed_by=self.request.user,
            is_closed=True,
            closed_at=timezone.now()
        )

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        if not request.user.is_superuser and request.user.role not in ['ADMIN', 'LOCAL_ADMIN']:
             return Response({'error': 'No tiene permisos para reaperturar periodos cerrados.'}, status=status.HTTP_403_FORBIDDEN)
        
        close = self.get_object()
        close.is_closed = False
        close.save()
        return Response({'status': 'reopened', 'message': f'Periodo {close.month}/{close.year} reaperturado.'})


class AccountViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = 'institution'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Optional: Return only root accounts for tree view
        if self.request.query_params.get('roots') == 'true':
            queryset = queryset.filter(parent__isnull=True)
            
        return queryset

class JournalEntryViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = 'institution'

    def get_queryset(self):
        return super().get_queryset().order_by('-date', '-id')

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def post_entry(self, request, pk=None):
        entry = self.get_object()
        if entry.state == 'POSTED':
            return Response({'error': 'El asiento ya está asentado.'}, status=status.HTTP_400_BAD_REQUEST)
            
        if not entry.is_balanced:
            return Response({'error': f'El asiento está descuadrado (D: {entry.total_debit} | C: {entry.total_credit}).'}, status=status.HTTP_400_BAD_REQUEST)
            
        entry.state = 'POSTED'
        entry.save()
        return Response({'status': 'posted'})

    @action(detail=True, methods=['post'])
    def cancel_entry(self, request, pk=None):
        entry = self.get_object()
        if entry.state == 'CANCELLED':
            return Response({'error': 'El asiento ya está anulado.'}, status=status.HTTP_400_BAD_REQUEST)
            
        entry.state = 'CANCELLED'
        entry.save()
        return Response({'status': 'cancelled'})

class BankViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = 'institution'

    def get_queryset(self):
        return super().get_queryset().order_by('name')

class BankAccountViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = 'institution'

    def get_queryset(self):
        return super().get_queryset().select_related('bank', 'linked_account').order_by('bank__name', 'account_number')

from django.db.models import Sum, Q

class ReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        # Protegemos reportes que están en desarrollo en el frontend
        if self.action in ['ats']: # Añadir más si es necesario
            return [IsGlobalAdmin()]
        return [permissions.IsAuthenticated()]

    def list(self, request):
        return Response([])

    @action(detail=False, methods=['get'])
    def balance_sheet(self, request):
        user = request.user
        # Date range filter if needed
        
        # 1. Assets (ACTIVO)
        assets = self._get_account_tree(user.institution, 'ASSET')
        # 2. Liabilities (PASIVO)
        liabilities = self._get_account_tree(user.institution, 'LIABILITY')
        # 3. Equity (PATRIMONIO)
        equity = self._get_account_tree(user.institution, 'EQUITY')

        # Calculate totals
        total_assets = self._get_group_total(assets)
        total_liabilities = self._get_group_total(liabilities)
        total_equity = self._get_group_total(equity)
        
        # Calculate Current Net Income (Income - Expense) to add to Equity (Retained Earnings)
        net_income = self._calculate_net_income(user.institution)
        
        return Response({
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'net_income': net_income,
            'total_equity_and_liabilities': total_liabilities + total_equity + net_income
        })

    @action(detail=False, methods=['get'])
    def income_statement(self, request):
        user = user = request.user
        
        income = self._get_account_tree(user.institution, 'INCOME')
        expenses = self._get_account_tree(user.institution, 'EXPENSE')
        
        total_income = self._get_group_total(income)
        total_expenses = self._get_group_total(expenses)
        
        return Response({
            'income': income,
            'expenses': expenses,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': total_income - total_expenses
        })

    @action(detail=False, methods=['get'])
    def trial_balance(self, request):
        """
        Balance de Comprobación: Sumas y Saldos de todas las cuentas con movimiento.
        """
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        from .models import Account, JournalItem
        from django.db.models import Sum

        accounts = Account.objects.filter(institution=user.institution).order_by('code')
        data = []

        for acc in accounts:
            items = JournalItem.objects.filter(account=acc, journal_entry__state='POSTED')
            if start_date:
                items = items.filter(journal_entry__date__gte=start_date)
            if end_date:
                items = items.filter(journal_entry__date__lte=end_date)
            
            totals = items.aggregate(
                sum_debit=Sum('debit'),
                sum_credit=Sum('credit')
            )
            
            debit = totals['sum_debit'] or Decimal('0.00')
            credit = totals['sum_credit'] or Decimal('0.00')
            
            if debit == 0 and credit == 0:
                continue

            if acc.account_type in ['ASSET', 'EXPENSE']:
                balance = debit - credit
            else:
                balance = credit - debit

            data.append({
                'id': acc.id,
                'code': acc.code,
                'name': acc.name,
                'type': acc.account_type,
                'sum_debit': debit,
                'sum_credit': credit,
                'balance': balance
            })

        return Response(data)

    def _calculate_net_income(self, institution):
        from .models import JournalItem
        # Income (Credit is positive)
        income_credits = JournalItem.objects.filter(
            account__institution=institution,
            account__account_type='INCOME',
            journal_entry__state='POSTED'
        ).aggregate(Sum('credit'))['credit__sum'] or 0
        income_debits = JournalItem.objects.filter(
            account__institution=institution,
            account__account_type='INCOME',
            journal_entry__state='POSTED'
        ).aggregate(Sum('debit'))['debit__sum'] or 0
        total_income = income_credits - income_debits

        # Expense (Debit is positive)
        expense_debits = JournalItem.objects.filter(
            account__institution=institution,
            account__account_type='EXPENSE',
            journal_entry__state='POSTED'
        ).aggregate(Sum('debit'))['debit__sum'] or 0
        expense_credits = JournalItem.objects.filter(
            account__institution=institution,
            account__account_type='EXPENSE',
            journal_entry__state='POSTED'
        ).aggregate(Sum('credit'))['credit__sum'] or 0
        total_expense = expense_debits - expense_credits

        return total_income - total_expense

    @action(detail=False, methods=['get'])
    def ats(self, request):
        from accounting.sri.ats import ATSGenerator
        from django.http import HttpResponse

        user = request.user
        year = int(request.query_params.get('year', 2024))
        month = int(request.query_params.get('month', 1))

        generator = ATSGenerator(user.institution, year, month)
        xml_content = generator.generate_xml()

        response = HttpResponse(xml_content, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="ATS_{year}_{month:02d}.xml"'
        return response

    @action(detail=False, methods=['get'])
    def ledger(self, request):
        user = request.user
        account_id = request.query_params.get('account_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not account_id:
            return Response({'error': 'account_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        from .models import JournalItem, Account
        
        try:
            account = Account.objects.get(id=account_id, institution=user.institution)
        except Account.DoesNotExist:
            return Response({'error': 'Cuenta no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        queryset = JournalItem.objects.filter(
            account=account, 
            journal_entry__state='POSTED'
        ).select_related('journal_entry').order_by('journal_entry__date', 'id')

        # Calculate previous balance
        previous_debits = Decimal(0)
        previous_credits = Decimal(0)
        
        if start_date:
            from django.db.models import Sum
            prev_items = JournalItem.objects.filter(
                account=account,
                journal_entry__state='POSTED',
                journal_entry__date__lt=start_date
            )
            previous_debits = prev_items.aggregate(Sum('debit'))['debit__sum'] or Decimal(0)
            previous_credits = prev_items.aggregate(Sum('credit'))['credit__sum'] or Decimal(0)
            
            queryset = queryset.filter(journal_entry__date__gte=start_date)

        if end_date:
            queryset = queryset.filter(journal_entry__date__lte=end_date)

        initial_balance = Decimal(0)
        if account.account_type in ['ASSET', 'EXPENSE']:
            initial_balance = previous_debits - previous_credits
        else:
            initial_balance = previous_credits - previous_debits

        data = []
        running_balance: Decimal = initial_balance

        for item in queryset:
            if account.account_type in ['ASSET', 'EXPENSE']:
                running_balance += Decimal(item.debit - item.credit)
            else:
                running_balance += Decimal(item.credit - item.debit)

            data.append({
                'id': item.id,
                'date': item.journal_entry.date.strftime('%Y-%m-%d'),
                'journal_id': item.journal_entry.id,
                'description': item.description or item.journal_entry.description,
                'reference': item.journal_entry.reference,
                'debit': item.debit,
                'credit': item.credit,
                'balance': running_balance
            })

        return Response({
            'account_id': account.id,
            'account_code': account.code,
            'account_name': account.name,
            'initial_balance': initial_balance,
            'transactions': data,
            'final_balance': running_balance
        })

    def _get_account_tree(self, institution, account_type):
        from .models import Account
        # Fetch all accounts of this type
        accounts = Account.objects.filter(institution=institution, account_type=account_type).order_by('code')
        
        # Build Map
        # Build Map
        acc_map = {acc.id: {'id': acc.id, 'code': acc.code, 'name': acc.name, 'parent': acc.parent_id, 'children': [], 'balance': Decimal(0)} for acc in accounts}
        
        roots = []
        
        # 1. Calculate Allowances/Balances for Leaf Nodes
        from .models import JournalItem
        
        for acc in accounts:
            node = acc_map[acc.id]
            # Get Balance from DB
            debits = JournalItem.objects.filter(account=acc, journal_entry__state='POSTED').aggregate(Sum('debit'))['debit__sum'] or 0
            credits = JournalItem.objects.filter(account=acc, journal_entry__state='POSTED').aggregate(Sum('credit'))['credit__sum'] or 0
            
            if account_type in ['ASSET', 'EXPENSE']:
                node['balance'] = debits - credits
            else: # LIABILITY, EQUITY, INCOME
                node['balance'] = credits - debits

        # 2. Build Tree and Aggregate up
        # We do this by iterating backwards by level (deepest first) or just naive recursion?
        # Naive approach: Attach to parents
        for acc in accounts:
            node = acc_map[acc.id]
            if node['parent']:
                if node['parent'] in acc_map:
                    parent = acc_map[node['parent']]
                    children = parent['children']
                    if isinstance(children, list):
                        children.append(node)
            else:
                roots.append(node)
                
        # 3. Propagate Balances (Post-order traversal)
        for root in roots:
            self._propagate_balance(root)
            
        return roots

    def _propagate_balance(self, node):
        child_total = Decimal(0)
        for child in node['children']:
            self._propagate_balance(child)
            child_total += child['balance']
        
        node['balance'] += child_total

    def _get_group_total(self, tree_nodes):
        total = Decimal(0)
        for node in tree_nodes:
            total += node['balance']
        return total

class FixedAssetViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = FixedAsset.objects.all()
    serializer_class = FixedAssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = 'institution'

    def get_queryset(self):
        return super().get_queryset().order_by('-purchase_date')

    @action(detail=True, methods=['post'])
    def calculate_depreciation(self, request, pk=None):
        asset = self.get_object()
        
        # Simple straight-line depreciation logic
        monthly_depreciation = (asset.purchase_price - asset.salvage_value) / Decimal(str(asset.useful_life_years * 12))
        
        # Calculate how many months pending
        last_depreciation = asset.depreciations.first()
        start_date = last_depreciation.date if last_depreciation else asset.purchase_date
        
        today = timezone.now().date()
        
        months_passed = (today.year - start_date.year) * 12 + today.month - start_date.month
        
        if months_passed <= 0:
            return Response({'error': 'No ha pasado un mes desde la última depreciación o compra.'}, status=status.HTTP_400_BAD_REQUEST)
            
        total_to_depreciate = monthly_depreciation * Decimal(str(months_passed))
        
        balance_to_depreciate = (asset.purchase_price - asset.salvage_value) - asset.accumulated_depreciation
        
        if asset.accumulated_depreciation + total_to_depreciate > (asset.purchase_price - asset.salvage_value):
            total_to_depreciate = balance_to_depreciate
            
        if total_to_depreciate <= 0 or balance_to_depreciate <= 0:
            return Response({'error': 'Activo totalmente depreciado.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create Journal Entry
        entry = JournalEntry.objects.create(
            institution=request.user.institution,
            date=today,
            description=f"Depreciación de activo: {asset.name} ({months_passed} meses)",
            state='POSTED',
            created_by=request.user
        )
        
        from .models import JournalItem
        # Debit Expense
        JournalItem.objects.create(
            journal_entry=entry,
            account=asset.account_expense,
            debit=total_to_depreciate,
            credit=Decimal('0.00'),
            description=f"Depreciación {asset.name}"
        )
        
        # Credit Accumulated Depreciation
        JournalItem.objects.create(
            journal_entry=entry,
            account=asset.account_depreciation,
            debit=Decimal('0.00'),
            credit=total_to_depreciate,
            description=f"Depreciación {asset.name}"
        )
        
        # Record Depreciation
        dep = Depreciation.objects.create(
            asset=asset,
            date=today,
            amount=total_to_depreciate,
            journal_entry=entry,
            notes=f"Depreciación por {months_passed} meses"
        )
        
        # Update Asset
        asset.accumulated_depreciation += total_to_depreciate
        asset.save()
        
        return Response({'status': 'ok', 'amount': total_to_depreciate, 'months': months_passed})

class AccountingConfigViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = AccountingConfig.objects.all()
    serializer_class = AccountingConfigSerializer
    permission_classes = [IsGlobalAdmin]
    tenant_field = 'institution'

    def get_queryset(self):
        return super().get_queryset().select_related('account')

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)
