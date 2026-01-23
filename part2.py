
class TicketCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TicketCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TicketComment.objects.all()
        ticket_id = self.request.query_params.get('ticket')
        if ticket_id:
            queryset = queryset.filter(ticket_id=ticket_id)
        
        # Security check: User must be related to ticket unless staff
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(ticket__requester=self.request.user)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TicketAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = TicketAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TicketAttachment.objects.all()
        ticket_id = self.request.query_params.get('ticket')
        if ticket_id:
            queryset = queryset.filter(ticket_id=ticket_id)
            
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(ticket__requester=self.request.user)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
