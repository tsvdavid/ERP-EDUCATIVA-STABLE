from rest_framework import viewsets
from .models import KnowledgeCategory, KnowledgeArticle
from .serializers import KnowledgeCategorySerializer, KnowledgeArticleSerializer

class KnowledgeCategoryViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeCategory.objects.all()
    serializer_class = KnowledgeCategorySerializer

    def get_queryset(self):
        return self.queryset.filter(institution=self.request.user.institution)

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)

class KnowledgeArticleViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeArticle.objects.all()
    serializer_class = KnowledgeArticleSerializer

    def get_queryset(self):
        return self.queryset.filter(category__institution=self.request.user.institution)
