from rest_framework import serializers
from .models import ServiceCatalog, Ticket, Workflow, PassStep, TicketSurvey, TicketComment, TicketAttachment

class TicketCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = TicketComment
        fields = '__all__'
        read_only_fields = ('author', 'created_at')

class TicketAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = TicketAttachment
        fields = '__all__'
        read_only_fields = ('uploaded_by', 'filename', 'created_at')
from users.serializers import UserSerializer

class ServiceCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCatalog
        fields = '__all__'
        read_only_fields = ('institution',)

class PassStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassStep
        fields = '__all__'

class WorkflowSerializer(serializers.ModelSerializer):
    steps = PassStepSerializer(many=True, read_only=True)
    
    class Meta:
        model = Workflow
        fields = '__all__'

class TicketSurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketSurvey
        fields = '__all__'
        read_only_fields = ('ticket', 'created_at')

class TicketSerializer(serializers.ModelSerializer):
    requester_data = UserSerializer(source='requester', read_only=True)
    assigned_to_data = UserSerializer(source='assigned_to', read_only=True)
    category_name = serializers.SerializerMethodField()
    survey = TicketSurveySerializer(read_only=True)
    comments = TicketCommentSerializer(many=True, read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)
    
    def get_category_name(self, obj):
        if not obj.category:
            return "N/A"
        
        # Build path
        path = [obj.category.name]
        parent = obj.category.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
            
        return " > ".join(path)
    
    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('requester', 'institution', 'current_step', 'created_at', 'updated_at', 'due_date')


