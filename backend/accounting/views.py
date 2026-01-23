from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Account, FiscalYear, JournalEntry
from .serializers import AccountSerializer, FiscalYearSerializer, JournalEntrySerializer

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Account.objects.filter(institution=user.institution)
        
        # Optional: Return only root accounts for tree view
        if self.request.query_params.get('roots') == 'true':
            queryset = queryset.filter(parent__isnull=True)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)

class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JournalEntry.objects.filter(institution=self.request.user.institution).order_by('-date', '-id')

    def perform_create(self, serializer):
        serializer.save(
            institution=self.request.user.institution,
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

from django.db.models import Sum, Q

class ReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

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

    def _get_account_tree(self, institution, account_type):
        from .models import Account
        # Fetch all accounts of this type
        accounts = Account.objects.filter(institution=institution, account_type=account_type).order_by('code')
        
        # Build Map
        acc_map = {acc.id: {'id': acc.id, 'code': acc.code, 'name': acc.name, 'parent': acc.parent_id, 'children': [], 'balance': 0} for acc in accounts}
        
        roots = []
        
        # 1. Calculate Allowances/Balances for Leaf Nodes
        from .models import JournalItem
        
        for acc in accounts:
            node = acc_map[acc.id]
            # Get Balance from DB
            debits = JournalItem.objects.filter(account=acc, journal_entry__state='POSTED').aggregate(Sum('debit'))['debit__sum'] or 0
            credits = JournalItem.objects.filter(account=acc, journal_entry__state='POSTED').aggregate(Sum('credit'))['credit__sum'] or 0
            
            if account_type in ['ASSET', 'EXPENSE']:
                node['balance'] = float(debits - credits)
            else: # LIABILITY, EQUITY, INCOME
                node['balance'] = float(credits - debits)

        # 2. Build Tree and Aggregate up
        # We do this by iterating backwards by level (deepest first) or just naive recursion?
        # Naive approach: Attach to parents
        for acc in accounts:
            node = acc_map[acc.id]
            if node['parent']:
                if node['parent'] in acc_map:
                    parent = acc_map[node['parent']]
                    parent['children'].append(node)
            else:
                roots.append(node)
                
        # 3. Propagate Balances (Post-order traversal)
        for root in roots:
            self._propagate_balance(root)
            
        return roots

    def _propagate_balance(self, node):
        child_total = 0
        for child in node['children']:
            self._propagate_balance(child)
            child_total += child['balance']
        
        node['balance'] += child_total

    def _get_group_total(self, tree_nodes):
        total = 0
        for node in tree_nodes:
            total += node['balance']
        return total
