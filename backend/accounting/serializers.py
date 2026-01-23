from rest_framework import serializers
from .models import Account, FiscalYear, JournalEntry, JournalItem

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
