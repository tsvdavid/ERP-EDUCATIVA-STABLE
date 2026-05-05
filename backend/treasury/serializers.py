from rest_framework import serializers
from .models import PaymentConcept, PaymentMethod, Invoice, InvoiceDetail, Payment, StudentAccount, Charge, CreditNote, DebitNote, Customer
from users.serializers import UserSerializer
from notifications.models import EmailLog

class PaymentConceptSerializer(serializers.ModelSerializer):
    iva_rate = serializers.DecimalField(max_digits=4, decimal_places=2, required=False)
    
    class Meta:
        model = PaymentConcept
        fields = '__all__'

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class InvoiceDetailSerializer(serializers.ModelSerializer):
    concept_name = serializers.CharField(source='concept.name', read_only=True)
    
    class Meta:
        model = InvoiceDetail
        fields = ('id', 'concept', 'concept_name', 'quantity', 'unit_price', 'subtotal')

class InvoiceSerializer(serializers.ModelSerializer):
    customer_details = CustomerSerializer(source='customer', read_only=True)
    emitter_name = serializers.CharField(source='institution.name', read_only=True)
    student_name = serializers.SerializerMethodField()
    was_sent = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('number', 'issue_date', 'status', 'created_by', 'created_at', 'subtotal_0', 'subtotal_15', 'iva_total', 'total', 'institution')

    def __init__(self, *args, **kwargs):
        super(InvoiceSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            inst_id = request.user.institution_id
            if 'customer' in self.fields:
                self.fields['customer'].queryset = Customer.objects.filter(institution_id=inst_id)

    def get_was_sent(self, obj):
        return obj.email_status == 'SENT'

    def get_student_name(self, obj):
        if obj.student:
            return f"{obj.student.first_name} {obj.student.last_name}".strip()
        if obj.customer:
            return f"{obj.customer.first_name} {obj.customer.last_name}".strip()
        return obj.client_name or "Consumidor Final"

class ChargeSerializer(serializers.ModelSerializer):
    concept_detail = PaymentConceptSerializer(source='concept', read_only=True)
    class Meta:
        model = Charge
        fields = '__all__'
        read_only_fields = ('institution',)

    def __init__(self, *args, **kwargs):
        super(ChargeSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            inst_id = request.user.institution_id
            if 'customer' in self.fields:
                self.fields['customer'].queryset = Customer.objects.filter(institution_id=inst_id)
            if 'student' in self.fields:
                from users.models import User
                self.fields['student'].queryset = User.objects.filter(institution_id=inst_id, role='STUDENT')
            if 'concept' in self.fields:
                self.fields['concept'].queryset = PaymentConcept.objects.filter(institution_id=inst_id)

class CreateInvoiceSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(required=False, allow_null=True)
    customer_id = serializers.IntegerField(required=False, allow_null=True)
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
        read_only_fields = ('number', 'issue_date', 'status', 'created_at', 'institution')

    def __init__(self, *args, **kwargs):
        super(CreditNoteSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            inst_id = request.user.institution_id
            if 'invoice' in self.fields:
                self.fields['invoice'].queryset = Invoice.objects.filter(institution_id=inst_id)

class DebitNoteSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.number', read_only=True)
    
    class Meta:
        model = DebitNote
        fields = '__all__'
        read_only_fields = ('number', 'issue_date', 'status', 'created_at', 'institution')

    def __init__(self, *args, **kwargs):
        super(DebitNoteSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            inst_id = request.user.institution_id
            if 'invoice' in self.fields:
                self.fields['invoice'].queryset = Invoice.objects.filter(institution_id=inst_id)


class EmailLogSerializer(serializers.ModelSerializer):
    sent_by_name = serializers.SerializerMethodField()
    send_type_display = serializers.CharField(source='get_send_type_display', read_only=True)
    
    class Meta:
        model = EmailLog
        fields = ('id', 'recipient', 'subject', 'status', 'send_type', 'send_type_display', 'sent_by_name', 'sent_at', 'created_at', 'error_message')

    def get_sent_by_name(self, obj):
        if obj.sent_by:
            return obj.sent_by.get_full_name() or obj.sent_by.username
        return "Sistema"
