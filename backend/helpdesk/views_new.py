from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

# Project imports
from core.tenancy.viewsets import BaseTenantViewSet
from users.tenant_mixins import InstitutionFilterMixin
from .models import ServiceCatalog, Ticket, Workflow, TicketSurvey, TicketComment, TicketAttachment
from users.models import Institution
from .serializers import (
    ServiceCatalogSerializer,
    TicketSerializer,
    WorkflowSerializer,
    TicketSurveySerializer,
    TicketCommentSerializer,
    TicketAttachmentSerializer,
)


class ServiceCatalogViewSet(viewsets.ModelViewSet):
    queryset = ServiceCatalog.objects.unscoped().filter(is_active=True)
    serializer_class = ServiceCatalogSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return self.queryset.none()
        return self.queryset.filter(institution=tenant)

    def perform_create(self, serializer):
        inst = getattr(self.request, 'tenant', None)
        if not inst:
            if self.request.user.is_superuser:
                inst = Institution.objects.first()
            if not inst:
                raise ValidationError({
                    "institution": "User must belong to an institution to create catalog items."
                })
        serializer.save(institution=inst)


class TicketViewSet(BaseTenantViewSet, InstitutionFilterMixin):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Tenant is enforced by BaseTenantViewSet; filter by tenant
        tenant = self.request.tenant
        user = self.request.user
        if user.role in ['ADMIN', 'RECTOR', 'SECRETARY'] or user.is_superuser:
            return Ticket.objects.filter(institution=tenant)
        return Ticket.objects.filter(requester=user, institution=tenant)

    def perform_create(self, serializer):
        # BaseTenantViewSet injects tenant; just set requester
        serializer.save(requester=self.request.user, institution=self.request.tenant)

    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        ticket = self.get_object()
        return Response(
            {'error': 'Ticket must be resolved to rate'},
            status=status.HTTP_400_BAD_REQUEST,
        )
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
            return Response(
                {'error': 'Cannot reopen active ticket'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ticket.status = 'REOPENED'
        ticket.reopen_count += 1
        ticket.save()
        return Response({'status': 'Ticket reopened'})


class WorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return Workflow.objects.none()
        return Workflow.objects.unscoped().filter(institution=tenant)

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            raise ValidationError('No se pudo determinar el tenant activo.')
        serializer.save(institution=tenant)

    def perform_update(self, serializer):
        instance = serializer.instance
        serializer.save(institution=instance.institution)


class TicketCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TicketCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TicketComment.objects.unscoped()
        tenant = getattr(self.request, 'tenant', None)
        if tenant is None:
            return queryset.none()
        queryset = queryset.filter(ticket__institution=tenant)
        ticket_id = self.request.query_params.get('ticket')
        if ticket_id:
            queryset = queryset.filter(ticket_id=ticket_id)
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(ticket__requester=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, institution=self.request.tenant)

    def perform_update(self, serializer):
        instance = serializer.instance
        serializer.save(institution=instance.institution, author=instance.author)


class TicketAttachmentViewSet(InstitutionFilterMixin, BaseTenantViewSet):
    serializer_class = TicketAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = self.request.tenant
        queryset = TicketAttachment.objects.filter(ticket__institution=tenant)
        ticket_id = self.request.query_params.get('ticket')
        if ticket_id:
            queryset = queryset.filter(ticket_id=ticket_id)
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(ticket__requester=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user, institution=self.request.tenant)
