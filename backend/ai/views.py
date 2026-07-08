from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AIProviderConfig
from .serializers import AIProviderConfigSerializer
from .services import AIServiceFactory

class AIConfigViewSet(viewsets.ModelViewSet):
    queryset = AIProviderConfig.objects.unscoped()
    serializer_class = AIProviderConfigSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None) or getattr(self.request.user, 'institution', None)
        if tenant is None:
            return self.queryset.none()
        return self.queryset.filter(institution=tenant)

    @action(detail=False, methods=['post'])
    def test_connection(self, request):
        institution = getattr(request, 'tenant', None) or getattr(request.user, 'institution', None)
        if institution is None:
            return Response({"status": "error", "message": "No tenant context available."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            provider = AIServiceFactory.get_provider(institution)
            response = provider.generate_completion("Hola, responde con la palabra 'OK' si recibes este mensaje.", system_prompt="Eres un asistente de pruebas.")
            return Response({"status": "success", "response": response}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class assistantViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def ask(self, request):
        prompt = request.data.get('prompt')
        context = request.data.get('context', '')
        
        if not prompt:
            return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            provider = AIServiceFactory.get_provider(request.user.institution)
            system_prompt = f"Eres Eduka AI, un asistente de aprendizaje. Contexto de la lección: {context}"
            response = provider.generate_completion(prompt, system_prompt=system_prompt)
            return Response({"response": response}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def summarize(self, request):
        content = request.data.get('content')
        if not content:
            return Response({"error": "Content is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            provider = AIServiceFactory.get_provider(request.user.institution)
            prompt = f"Resume el siguiente contenido educativo de forma concisa y profesional, usando puntos clave:\n\n{content}"
            response = provider.generate_completion(prompt, system_prompt="Eres un experto en pedagogía y síntesis de información.")
            return Response({"summary": response}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
