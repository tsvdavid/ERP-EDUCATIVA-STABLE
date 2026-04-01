from rest_framework import serializers
from .models import KnowledgeCategory, KnowledgeArticle

class KnowledgeArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeArticle
        fields = '__all__'

class KnowledgeCategorySerializer(serializers.ModelSerializer):
    articles = KnowledgeArticleSerializer(many=True, read_only=True)
    class Meta:
        model = KnowledgeCategory
        fields = '__all__'
        read_only_fields = ('institution',)
