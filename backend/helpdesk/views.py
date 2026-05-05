from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import ServiceCatalog, Ticket, Workflow, TicketSurvey, TicketComment, TicketAttachment
from users.models import Institution, User
from rest_framework.exceptions import ValidationError
from .serializers import (
    ServiceCatalogSerializer,
    TicketSerializer,
    WorkflowSerializer,
    TicketSurveySerializer,
    TicketCommentSerializer,
    TicketAttachmentSerializer
)
from users.permissions import IsAdminUser, IsLocalAdminUser, IsAcademicStaff, IsTreasuryStaff, IsHealthStaff
from users.tenant_mixins import InstitutionFilterMixin
import reportlab

class ServiceCatalogViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = ServiceCatalog.objects.filter(is_active=True)
    serializer_class = ServiceCatalogSerializer
    tenant_field = 'institution'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsLocalAdminUser()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        inst = self.request.user.institution
        if not inst:
            # BLOQUEO: Eliminado fallback Institution.objects.first() para superusers.
            # Los superusers deben usar el header X-Institution-ID si no tienen inst vinculada.
            raise ValidationError({"institution": "Debe pertenecer a una institución o especificar una para crear ítems de catálogo."})

        serializer.save(institution=inst)

class TicketViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = 'institution'

    def get_queryset(self):
        user = self.request.user
        # Optimize query with select_related
        qs = super().get_queryset().select_related('requester', 'assigned_to', 'category', 'institution', 'current_step')

        # If admin/staff (Agent), see all or assigned. If student/teacher, only requested.
        if user.role in ['ADMIN', 'RECTOR', 'SECRETARY'] or user.is_superuser:
            return qs
        else:
            return qs.filter(requester=user)

    def perform_create(self, serializer):
        inst = self.request.user.institution
        if not inst:
             # BLOQUEO: Eliminado fallback Institution.objects.first()
             raise ValidationError({"institution": "Debe pertenecer a una institución para crear tickets."})
                
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

    @action(detail=True, methods=['post'])
    def take_ticket(self, request, pk=None):
        ticket = self.get_object()
        user = request.user
        
        if ticket.assigned_to:
            return Response({'error': 'Ticket ya está asignado'}, status=status.HTTP_400_BAD_REQUEST)
            
        ticket.assigned_to = user
        if ticket.status == 'OPEN':
             ticket.status = 'IN_PROGRESS'
        ticket.save()
        return Response({'status': 'Ticket asignado exitosamente', 'assigned_to': user.id})

class WorkflowViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    serializer_class = WorkflowSerializer
    permission_classes = [permissions.IsAdminUser]
    tenant_field = 'institution'
    
    def get_queryset(self):
        return super().get_queryset()
