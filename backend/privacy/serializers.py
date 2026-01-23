from rest_framework import serializers
from .models import PolicyVersion, ConsentRecord, ARCORequest, TreatmentActivity, DataBreach
from users.serializers import UserSerializer

class PolicyVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyVersion
        fields = '__all__'

class ConsentRecordSerializer(serializers.ModelSerializer):
    policy_name = serializers.CharField(source='policy.name', read_only=True)
    
    class Meta:
        model = ConsentRecord
        fields = '__all__'
        read_only_fields = ('user', 'timestamp', 'ip_address', 'user_agent')

class ARCORequestSerializer(serializers.ModelSerializer):
    requester_data = UserSerializer(source='requester', read_only=True)
    
    class Meta:
        model = ARCORequest
        fields = '__all__'
        read_only_fields = ('requester', 'institution', 'status', 'created_at', 'updated_at', 'deadline', 'response_content')

class TreatmentActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentActivity
        fields = '__all__'

class DataBreachSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataBreach
        fields = '__all__'
