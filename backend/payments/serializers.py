from rest_framework import serializers
from payments.models import Transaction, PaymentLog, PaymentGatewayConfig

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'amount', 'currency', 'status', 'gateway_name', 
            'reference_id', 'description', 'voucher_file', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']

class CheckoutSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3, default="USD")
    gateway_name = serializers.CharField(max_length=50) # 'stripe', 'payphone', 'bank_transfer'
    reference_id = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(max_length=255, required=False)
    voucher_file = serializers.FileField(required=False)

class PaymentGatewayConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGatewayConfig
        fields = ['id', 'institution', 'gateway_name', 'is_active', 'is_test_mode', 'credentials']
        read_only_fields = ['id', 'institution']
