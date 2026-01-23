from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ServiceCatalog, Ticket, Workflow, TicketSurvey, TicketComment, TicketAttachment
from users.models import Institution
from rest_framework.exceptions import ValidationError
from .serializers import (
    ServiceCatalogSerializer, 
    TicketSerializer, 
    WorkflowSerializer, 
    TicketSurveySerializer,
    TicketCommentSerializer,
    TicketAttachmentSerializer
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
        if user.role in ['ADMIN', 'RECTOR', 'SECRETARY'] or user.is_superuser: 
            if user.is_superuser and not user.institution:
                return Ticket.objects.all()
            return Ticket.objects.filter(institution=user.institution)
        else:
            return Ticket.objects.filter(requester=user)

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
        return Response({'status': 'Ticket reopened'})

class WorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        return Workflow.objects.filter(institution=self.request.user.institution)

class TicketCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TicketCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TicketComment.objects.all()
        ticket_id = self.request.query_params.get('ticket')
        if ticket_id:
            queryset = queryset.filter(ticket_id=ticket_id)
        
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(ticket__requester=self.request.user)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class TicketAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = TicketAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Allow linking to ticket via query param
        queryset = TicketAttachment.objects.all()
        ticket_id = self.request.query_params.get('ticket')
        if ticket_id:
            queryset = queryset.filter(ticket_id=ticket_id)
            
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(ticket__requester=self.request.user)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
