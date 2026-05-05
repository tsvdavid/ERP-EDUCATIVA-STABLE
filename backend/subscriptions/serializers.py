from rest_framework import serializers
from .models import Subscription, SubscriptionPayment, SubscriptionModule, Module, SubscriptionAuditLog, Plan, GlobalSettings

class PlanSerializer(serializers.ModelSerializer):
    included_modules_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Plan
        fields = '__all__'

    def get_included_modules_names(self, obj):
        return [m.name for m in obj.included_modules.all()]

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'

class SubscriptionModuleSerializer(serializers.ModelSerializer):
    module_name = serializers.ReadOnlyField(source='module.name')
    class Meta:
        model = SubscriptionModule
        fields = ['id', 'module', 'module_name', 'is_active', 'added_at']

class SubscriptionAuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')
    event_display = serializers.CharField(source='get_event_type_display', read_only=True)
    class Meta:
        model = SubscriptionAuditLog
        fields = '__all__'

class SubscriptionListSerializer(serializers.ModelSerializer):
    institution_name = serializers.ReadOnlyField(source='institution.name')
    plan_name = serializers.ReadOnlyField(source='plan.name')
    days_remaining = serializers.ReadOnlyField()
    billing_cycle_display = serializers.CharField(source='get_billing_cycle_display', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'institution', 'institution_name', 'plan', 'plan_name', 
            'status', 'start_date', 'next_billing_date', 'expiration_date', 
            'monthly_fee', 'price_override', 'billing_cycle', 'billing_cycle_display',
            'contract_duration_months', 'trial_duration_days', 'days_remaining'
        ]

class SubscriptionDetailSerializer(serializers.ModelSerializer):
    institution_name = serializers.ReadOnlyField(source='institution.name')
    plan_name = serializers.ReadOnlyField(source='plan.name')
    modules_detail = SubscriptionModuleSerializer(source='modules', many=True, read_only=True)
    audit_logs = SubscriptionAuditLogSerializer(many=True, read_only=True)
    days_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Subscription
        fields = '__all__'

class GlobalSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalSettings
        fields = '__all__'
