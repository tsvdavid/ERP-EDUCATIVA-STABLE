from rest_framework import serializers
from .models import Supplier, PurchaseInvoice, PurchaseItem, Withholding, PurchaseCreditNote, PurchaseDebitNote, PurchaseLiquidation, PurchaseLiquidationItem
from accounting.models import Account
from decimal import Decimal
from accounting.models import Account

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'
        read_only_fields = ['institution', 'created_at']

class PurchaseItemSerializer(serializers.ModelSerializer):
    expense_account_name = serializers.ReadOnlyField(source='expense_account.name')
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    
    class Meta:
        model = PurchaseItem
        fields = ['id', 'description', 'expense_account', 'expense_account_name', 'quantity', 'unit_price', 'subtotal', 'tax_rate']
        read_only_fields = ['subtotal']

class WithholdingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withholding
        fields = '__all__'

class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source='supplier.legal_name')
    items = PurchaseItemSerializer(many=True)
    withholding = WithholdingSerializer(read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = [
            'id', 'supplier', 'supplier_name', 'document_number', 'authorization_code',
            'issue_date', 'registration_date', 'sustento_tributario', 'payment_method',
            'subtotal_0', 'subtotal_15', 'subtotal_no_obj', 'iva', 'total', 'status',
            'items', 'withholding', 'created_at'
        ]
        read_only_fields = ['registration_date', 'created_by', 'created_at', 'status', 'total', 'iva', 'subtotal_0', 'subtotal_15', 'subtotal_no_obj']
        # Note: We make totals read_only because we want to calculate them from items? 
        # Or do we accept them from frontend? Usually frontend sends items, backend recalculates.

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Calculate totals from items
        subtotal_0: Decimal = Decimal('0.00')
        subtotal_15: Decimal = Decimal('0.00')
        iva: Decimal = Decimal('0.00')
        
        # We need to process items to calc totals BEFORE creating invoice if we want to store them
        # But we need invoice ID for items. So we create invoice with 0, then update.
        
        invoice = PurchaseInvoice.objects.create(**validated_data)
        
        for item_data in items_data:
            # Recalculate item line just in case
            qty = Decimal(str(item_data.get('quantity', 1)))
            price = Decimal(str(item_data.get('unit_price', 0)))
            tax_rate = Decimal(str(item_data.get('tax_rate', 0)))
            subtotal = qty * price
            
            PurchaseItem.objects.create(invoice=invoice, **item_data)
            
            if tax_rate == Decimal('0'):
                subtotal_0 += subtotal
            elif tax_rate == Decimal('15'):
                subtotal_15 += subtotal
                iva += subtotal * Decimal('0.15')
        
        invoice.subtotal_0 = subtotal_0
        invoice.subtotal_15 = subtotal_15
        invoice.iva = iva
        invoice.total = subtotal_0 + subtotal_15 + iva
        invoice.save()
        
        return invoice
    
    def update(self, instance, validated_data):
        # Prevent editing if validated
        if instance.status == 'VALIDATED':
             raise serializers.ValidationError("No se puede editar una factura validada.")

        items_data = validated_data.pop('items', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if items_data is not None:
            instance.items.all().delete()
            
            subtotal_0: Decimal = Decimal('0.00')
            subtotal_15: Decimal = Decimal('0.00')
            iva: Decimal = Decimal('0.00')
            
            for item_data in items_data:
                PurchaseItem.objects.create(invoice=instance, **item_data)
                
                qty = Decimal(str(item_data.get('quantity', 1)))
                price = Decimal(str(item_data.get('unit_price', 0)))
                tax_rate = Decimal(str(item_data.get('tax_rate', 0)))
                subtotal = qty * price
                
                if tax_rate == Decimal('0'):
                    subtotal_0 += subtotal
                elif tax_rate == Decimal('15'):
                    subtotal_15 += subtotal
                    iva += subtotal * Decimal('0.15')
            
            instance.subtotal_0 = subtotal_0
            instance.subtotal_15 = subtotal_15
            instance.iva = iva
            instance.total = subtotal_0 + subtotal_15 + iva
            
        instance.save()
        return instance

class PurchaseCreditNoteSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source='invoice.supplier.legal_name')
    invoice_number = serializers.ReadOnlyField(source='invoice.document_number')

    class Meta:
        model = PurchaseCreditNote
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'total']

class PurchaseDebitNoteSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source='invoice.supplier.legal_name')
    invoice_number = serializers.ReadOnlyField(source='invoice.document_number')

    class Meta:
        model = PurchaseDebitNote
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'total']

class PurchaseLiquidationItemSerializer(serializers.ModelSerializer):
    expense_account_name = serializers.ReadOnlyField(source='expense_account.name')
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    
    class Meta:
        model = PurchaseLiquidationItem
        fields = ['id', 'description', 'expense_account', 'expense_account_name', 'quantity', 'unit_price', 'subtotal', 'tax_rate']
        read_only_fields = ['subtotal']

class PurchaseLiquidationSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source='supplier.legal_name')
    items = PurchaseLiquidationItemSerializer(many=True)

    class Meta:
        model = PurchaseLiquidation
        fields = [
            'id', 'supplier', 'supplier_name', 'document_number', 'authorization_code',
            'issue_date', 'registration_date', 'sustento_tributario', 'payment_method',
            'subtotal_0', 'subtotal_15', 'subtotal_no_obj', 'iva', 'total', 'status',
            'items', 'created_at'
        ]
        read_only_fields = ['registration_date', 'created_by', 'created_at', 'status', 'total', 'iva', 'subtotal_0', 'subtotal_15', 'subtotal_no_obj']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        subtotal_0: Decimal = Decimal('0.00')
        subtotal_15: Decimal = Decimal('0.00')
        iva: Decimal = Decimal('0.00')
        
        liquidation = PurchaseLiquidation.objects.create(**validated_data)
        
        for item_data in items_data:
            qty = Decimal(str(item_data.get('quantity', 1)))
            price = Decimal(str(item_data.get('unit_price', 0)))
            tax_rate = Decimal(str(item_data.get('tax_rate', 0)))
            subtotal = qty * price
            
            PurchaseLiquidationItem.objects.create(liquidation=liquidation, **item_data)
            
            if tax_rate == Decimal('0'):
                subtotal_0 += subtotal
            elif tax_rate == Decimal('15'):
                subtotal_15 += subtotal
                iva += subtotal * Decimal('0.15')
        
        liquidation.subtotal_0 = subtotal_0
        liquidation.subtotal_15 = subtotal_15
        liquidation.iva = iva
        liquidation.total = subtotal_0 + subtotal_15 + iva
        liquidation.save()
        
        return liquidation
    
    def update(self, instance, validated_data):
        if instance.status == 'VALIDATED':
             raise serializers.ValidationError("No se puede editar una liquidación validada.")

        items_data = validated_data.pop('items', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if items_data is not None:
            instance.items.all().delete()
            
            subtotal_0: Decimal = Decimal('0.00')
            subtotal_15: Decimal = Decimal('0.00')
            iva: Decimal = Decimal('0.00')
            
            for item_data in items_data:
                PurchaseLiquidationItem.objects.create(liquidation=instance, **item_data)
                
                qty = Decimal(str(item_data.get('quantity', 1)))
                price = Decimal(str(item_data.get('unit_price', 0)))
                tax_rate = Decimal(str(item_data.get('tax_rate', 0)))
                subtotal = qty * price
                
                if tax_rate == Decimal('0'):
                    subtotal_0 += subtotal
                elif tax_rate == Decimal('15'):
                    subtotal_15 += subtotal
                    iva += subtotal * Decimal('0.15')
            
            instance.subtotal_0 = subtotal_0
            instance.subtotal_15 = subtotal_15
            instance.iva =iva
            instance.total = subtotal_0 + subtotal_15 + iva
            
        instance.save()
        return instance
