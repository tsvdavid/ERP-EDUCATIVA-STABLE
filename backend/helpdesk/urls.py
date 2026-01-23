from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_new import ServiceCatalogViewSet, TicketViewSet, WorkflowViewSet, TicketCommentViewSet, TicketAttachmentViewSet

router = DefaultRouter()
router.register(r'catalog', ServiceCatalogViewSet)
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'comments', TicketCommentViewSet, basename='ticket-comment')
router.register(r'attachments', TicketAttachmentViewSet, basename='ticket-attachment')

urlpatterns = [
    path('', include(router.urls)),
]
