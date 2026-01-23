from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ServiceCatalog, Ticket, Workflow, TicketSurvey
from users.models import Institution
from rest_framework.exceptions import ValidationError
from .serializers import (
    ServiceCatalogSerializer, 
    TicketSerializer, 
    WorkflowSerializer, 
    TicketSurveySerializer
)

class ServiceCatalogViewSet(viewsets.ModelViewSet):
    queryset = ServiceCatalog.objects.filter(is_active=True)
    serializer_class = ServiceCatalogSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        inst = self.request.user.institution
        if not inst:
            # Fallback for superusers without institution: grab the first one
            if self.request.user.is_superuser:
                inst = Institution.objects.first()
            
            if not inst:
                raise ValidationError({"institution": "User must belong to an institution to create catalog items."})
        
        serializer.save(institution=inst)

class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Optimize query with select_related
        qs = Ticket.objects.select_related('requester', 'assigned_to', 'category', 'institution', 'current_step')

        # If admin/staff (Agent), see all or assigned. If student/teacher, only requested.
        if user.role in ['ADMIN', 'RECTOR', 'SECRETARY'] or user.is_superuser: 
            if user.is_superuser and not user.institution:
                return qs.all()
            return qs.filter(institution=user.institution)
        else:
            return qs.filter(requester=user)

    def perform_create(self, serializer):
        inst = self.request.user.institution
        if not inst:
            if self.request.user.is_superuser:
                inst = Institution.objects.first()
            if not inst:
                raise ValidationError({"institution": "User must belong to an institution."})
                
        serializer.save(institution=inst, requester=self.request.user)

    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status != 'RESOLVED' and ticket.status != 'CLOSED':
            return Response({'error': 'Ticket must be resolved to rate'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = TicketSurveySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(ticket=ticket)
            # Auto-close resolved ticket after rating?
            if ticket.status == 'RESOLVED':
                ticket.status = 'CLOSED'
                ticket.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status not in ['RESOLVED', 'CLOSED']:
             return Response({'error': 'Cannot reopen active ticket'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status = 'REOPENED' 
        ticket.reopen_count += 1
        ticket.save()
        # Logic to notify agent would go here
        return Response({'status': 'Ticket reopened'})

class WorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        return Workflow.objects.filter(institution=self.request.user.institution)
