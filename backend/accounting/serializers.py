from rest_framework import serializers
from .models import Account, FiscalYear, JournalEntry, JournalItem, Bank, BankAccount, FixedAsset, Depreciation

class AccountSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ['id', 'code', 'name', 'account_type', 'parent', 'level', 'is_active', 'description', 'tax_id', 'children']
        read_only_fields = ['level', 'children']

    def get_children(self, obj):
        if obj.children.exists():
             return AccountSerializer(obj.children.all(), many=True).data
        return []

class FiscalYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalYear
        fields = '__all__'

class JournalItemSerializer(serializers.ModelSerializer):
    account_name = serializers.ReadOnlyField(source='account.name')
    account_code = serializers.ReadOnlyField(source='account.code')

    class Meta:
        model = JournalItem
        fields = ['id', 'account', 'account_code', 'account_name', 'description', 'debit', 'credit']

class JournalEntrySerializer(serializers.ModelSerializer):
    items = JournalItemSerializer(many=True)
    created_by_name = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = JournalEntry
        fields = ['id', 'date', 'description', 'reference', 'state', 'created_by', 'created_by_name', 'created_at', 'posted_at', 'items', 'total_debit', 'total_credit', 'is_balanced']
        read_only_fields = ['created_by', 'created_at', 'posted_at']

    def validate_date(self, value):
        from .models import FiscalYear
        request = self.context.get('request')
        if request and request.user.institution:
            try:
                fiscal_year = FiscalYear.objects.get(institution=request.user.institution, year=value.year)
                if fiscal_year.is_closed:
                    raise serializers.ValidationError(f"El año fiscal {value.year} está cerrado. No se pueden registrar asientos.")
            except FiscalYear.DoesNotExist:
                pass
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        entry = JournalEntry.objects.create(**validated_data)
        for item_data in items_data:
            JournalItem.objects.create(journal_entry=entry, **item_data)
        return entry

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # Update fields
        instance.date = validated_data.get('date', instance.date)
        instance.description = validated_data.get('description', instance.description)
        instance.reference = validated_data.get('reference', instance.reference)
        instance.save()
        
        if items_data is not None:
            # Replace items (simplistic approach for now)
            instance.items.all().delete()
            for item_data in items_data:
                 JournalItem.objects.create(journal_entry=instance, **item_data)
                 
        return instance

class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = '__all__'

class BankAccountSerializer(serializers.ModelSerializer):
    bank_name = serializers.ReadOnlyField(source='bank.name')
    linked_account_code = serializers.ReadOnlyField(source='linked_account.code')
    linked_account_name = serializers.ReadOnlyField(source='linked_account.name')
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    
    # Casting explícito a DecimalField para evitar errores DRF de Float vs Decimal en operaciones
    initial_balance = serializers.DecimalField(max_digits=15, decimal_places=2, coerce_to_string=False)

    class Meta:
        model = BankAccount
        fields = '__all__'

class DepreciationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depreciation
        fields = '__all__'

class FixedAssetSerializer(serializers.ModelSerializer):
    depreciations = DepreciationSerializer(many=True, read_only=True)
    account_asset_name = serializers.ReadOnlyField(source='account_asset.name')
    account_depreciation_name = serializers.ReadOnlyField(source='account_depreciation.name')
    account_expense_name = serializers.ReadOnlyField(source='account_expense.name')
    current_value = serializers.ReadOnlyField()

    class Meta:
        model = FixedAsset
        fields = '__all__'
        read_only_fields = ['institution', 'created_at']
