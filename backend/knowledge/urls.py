from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KnowledgeCategoryViewSet, KnowledgeArticleViewSet

router = DefaultRouter()
router.register(r'categories', KnowledgeCategoryViewSet)
router.register(r'articles', KnowledgeArticleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
