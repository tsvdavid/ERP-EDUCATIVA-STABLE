from rest_framework import serializers
from .models import Employee, Contract, WorkShift, Department, Position, Attendance, PayrollPeriod, PayrollRoll, PayrollItem

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ['institution']

class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    class Meta:
        model = Position
        fields = '__all__'
        read_only_fields = ['institution']

class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField(source='user.get_full_name')
    email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ['institution']

    def __init__(self, *args, **kwargs):
        super(EmployeeSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            tenant = request.tenant
            if 'user' in self.fields:
                from users.models import User
                self.fields['user'].queryset = User.objects.filter(institution=tenant)
            if 'department' in self.fields:
                self.fields['department'].queryset = Department.objects.filter(institution=tenant)
            if 'position' in self.fields:
                self.fields['position'].queryset = Position.objects.filter(institution=tenant)

class WorkShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShift
        fields = '__all__'
        read_only_fields = ['institution']

class ContractSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.user.get_full_name')
    position_name = serializers.ReadOnlyField(source='position.name')
    
    class Meta:
        model = Contract
        fields = '__all__'
        read_only_fields = ['institution']

    def __init__(self, *args, **kwargs):
        super(ContractSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            tenant = request.tenant
            if 'employee' in self.fields:
                self.fields['employee'].queryset = Employee.objects.filter(institution=tenant)
            if 'position' in self.fields:
                self.fields['position'].queryset = Position.objects.filter(institution=tenant)
            if 'work_shift' in self.fields:
                self.fields['work_shift'].queryset = WorkShift.objects.filter(institution=tenant)

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.user.get_full_name')
    
    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['institution']

class PayrollItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollItem
        fields = ['id', 'item_type', 'name', 'amount']

class PayrollRollSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.user.get_full_name')
    details = PayrollItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = PayrollRoll
        fields = '__all__'
        read_only_fields = ['institution']

    def __init__(self, *args, **kwargs):
        super(PayrollRollSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            tenant = request.tenant
            if 'employee' in self.fields:
                self.fields['employee'].queryset = Employee.objects.filter(institution=tenant)
            if 'period' in self.fields:
                self.fields['period'].queryset = PayrollPeriod.objects.filter(institution=tenant)

class PayrollPeriodSerializer(serializers.ModelSerializer):
    rolls_count = serializers.SerializerMethodField()
    month_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PayrollPeriod
        fields = '__all__'
        read_only_fields = ['institution', 'state', 'created_at', 'approved_at', 'approved_by']

    def get_rolls_count(self, obj):
        return obj.rolls.count()
    
    def get_month_name(self, obj):
        import calendar
        return calendar.month_name[obj.month]
