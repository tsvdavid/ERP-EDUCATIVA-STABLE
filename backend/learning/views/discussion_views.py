from rest_framework import viewsets, permissions
from ..models import DiscussionThread, DiscussionComment
from ..serializers import DiscussionThreadSerializer, DiscussionCommentSerializer
from users.tenant_mixins import InstitutionFilterMixin

class DiscussionThreadViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = DiscussionThread.objects.all()
    serializer_class = DiscussionThreadSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_lookup = 'course__institution'

    def get_queryset(self):
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class DiscussionCommentViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = DiscussionComment.objects.all()
    serializer_class = DiscussionCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_lookup = 'thread__course__institution'

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
