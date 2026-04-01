from rest_framework import serializers
from .models import PaymentConcept, PaymentMethod, Invoice, InvoiceDetail, Payment, StudentAccount, Charge, CreditNote, DebitNote
from users.serializers import UserSerializer

class PaymentConceptSerializer(serializers.ModelSerializer):
    iva_rate = serializers.DecimalField(max_digits=4, decimal_places=2, required=False)
    
    class Meta:
        model = PaymentConcept
        fields = '__all__'

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'

class InvoiceDetailSerializer(serializers.ModelSerializer):
    concept_name = serializers.CharField(source='concept.name', read_only=True)
    
    class Meta:
        model = InvoiceDetail
        fields = ('id', 'concept', 'concept_name', 'quantity', 'unit_price', 'subtotal')

class InvoiceSerializer(serializers.ModelSerializer):
    details = InvoiceDetailSerializer(many=True, read_only=True)
    emitter_name = serializers.CharField(source='institution.name', read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('number', 'issue_date', 'status', 'created_by', 'created_at', 'subtotal_0', 'subtotal_15', 'iva_total', 'total')

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

class ChargeSerializer(serializers.ModelSerializer):
    concept_detail = PaymentConceptSerializer(source='concept', read_only=True)
    class Meta:
        model = Charge
        fields = '__all__'

class CreateInvoiceSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    payment_method_id = serializers.IntegerField(required=False, allow_null=True)
    client_name = serializers.CharField(required=False, allow_blank=True)
    client_ruc = serializers.CharField(required=False, allow_blank=True)
    client_address = serializers.CharField(required=False, allow_blank=True)
    client_email = serializers.EmailField(required=False, allow_blank=True)
    concepts = serializers.ListField(
        child=serializers.DictField()
    ) 
    # expected format: [{'concept_id': 1, 'quantity': 1, 'charge_id': optional_int}, ...]

class StudentAccountSerializer(serializers.ModelSerializer):
    student_details = UserSerializer(source='student', read_only=True)
    
    class Meta:
        model = StudentAccount
        fields = '__all__'

class CreditNoteSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.number', read_only=True)
    
    class Meta:
        model = CreditNote
        fields = '__all__'
        read_only_fields = ('number', 'issue_date', 'status', 'created_at')

class DebitNoteSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.number', read_only=True)
    
    class Meta:
        model = DebitNote
        fields = '__all__'
        read_only_fields = ('number', 'issue_date', 'status', 'created_at')
