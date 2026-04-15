from rest_framework import viewsets, permissions
from ..models import DiscussionThread, DiscussionComment
from ..serializers import DiscussionThreadSerializer, DiscussionCommentSerializer

class DiscussionThreadViewSet(viewsets.ModelViewSet):
    queryset = DiscussionThread.objects.all()
    serializer_class = DiscussionThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(course__institution=self.request.user.institution)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class DiscussionCommentViewSet(viewsets.ModelViewSet):
    queryset = DiscussionComment.objects.all()
    serializer_class = DiscussionCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
