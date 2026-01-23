import os
import sys
import json
from io import StringIO
from django.core.management import call_command
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from rest_framework.parsers import MultiPartParser

User = get_user_model()

class BackupView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            # Create a buffer to capture dumpdata output
            buf = StringIO()
            # Exclude sessions and contenttypes to avoid issues on restore
            call_command('dumpdata', exclude=['auth.permission', 'contenttypes', 'sessions', 'admin.logentry'], stdout=buf)
            buf.seek(0)
            response = HttpResponse(buf.read(), content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="backup.json"'
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RestoreView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No se proporcionó ningún archivo'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Save temporary file
            file_path = os.path.join(settings.BASE_DIR, 'temp_restore.json')
            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)

            # Load data
            call_command('loaddata', file_path)
            
            # Clean up
            os.remove(file_path)
            
            return Response({'message': 'Restauración completada con éxito'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Error en la restauración: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserMaintenanceView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # List users (Teachers and Students only for safety?)
        # Or all users except the current admin
        users = User.objects.exclude(id=request.user.id).values('id', 'username', 'email', 'role', 'first_name', 'last_name')
        return Response(users)

    def delete(self, request):
        user_ids = request.data.get('user_ids', [])
        if not user_ids:
             return Response({'error': 'No se seleccionaron usuarios'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Prevent deleting self
            if request.user.id in user_ids:
                return Response({'error': 'No puedes eliminar tu propio usuario'}, status=status.HTTP_400_BAD_REQUEST)

            deleted_count, _ = User.objects.filter(id__in=user_ids).delete()
            return Response({'message': f'Se eliminaron {deleted_count} usuarios corectamente'}, status=status.HTTP_200_OK)
        except Exception as e:
             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        log_file = os.path.join(settings.BASE_DIR, 'django.log')
        if not os.path.exists(log_file):
            return Response({'log': 'El archivo de registro está vacío o no existe.'})
        
        try:
            with open(log_file, 'r') as f:
                # Read last 1000 lines or just all? All might be too big.
                # Let's read the whole thing for now, assuming regular rotation/cleaning
                content = f.read()
            return Response({'log': content})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        if not request.user.is_superuser:
             return Response({'error': 'Solo superusuarios pueden resetear el sistema'}, status=status.HTTP_403_FORBIDDEN)

        try:
            from django.db import transaction
            from django.apps import apps
            
            # List of apps to clear completely
            apps_to_clear = ['academic', 'communication', 'treasury', 'accounting', 'purchases', 'helpdesk']
            
            with transaction.atomic():
                # 1. Clear business apps
                for app_name in apps_to_clear:
                    app_config = apps.get_app_config(app_name)
                    for model in app_config.get_models():
                        model.objects.all().delete()
                
                # 2. Clear Users (except current admin)
                User = get_user_model()
                # Delete all users except the current one
                User.objects.exclude(id=request.user.id).delete()
                
                # 3. Handle Institution
                from users.models import Institution
                # Delete institutions not used by current user? 
                # Or just reset current user's institution to default?
                # If we delete all institutions, the user.institution FK might cascade or set null.
                # Ideally, we keep one default institution.
                
                # Let's clean institutions
                if request.user.institution:
                    # Keep only this one, or reset it?
                    # Let's reset it to "INSTITUCION PRUEBA"
                    inst = request.user.institution
                    inst.name = "INSTITUCION PRUEBA"
                    inst.save()
                    # Delete others
                    Institution.objects.exclude(id=inst.id).delete()
                else:
                    # Create default and assign
                    inst, _ = Institution.objects.get_or_create(
                        name="INSTITUCION PRUEBA",
                        defaults={'ruc': '9999999999001', 'email': 'admin@example.com'}
                    )
                    request.user.institution = inst
                    request.user.save()
                    # Delete others
                    Institution.objects.exclude(id=inst.id).delete()

            return Response({'message': 'La aplicación ha sido reseteada. Todos los datos han sido eliminados excepto su usuario.'}, status=status.HTTP_200_OK)
        except Exception as e:
             import traceback
             traceback.print_exc()
             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
