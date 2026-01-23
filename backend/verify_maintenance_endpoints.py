import os
import django
import json
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()

def verify_maintenance():
    print("Iniciando verificación del módulo de Mantenimiento...")
    
    # 1. Setup Admin User
    email = "admin_maintenance_test@example.com"
    password = "testpassword123"
    username = "admin_test_maint"
    
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
    else:
        user = User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Usuario administrador de prueba creado: {username}")

    client = APIClient()
    client.force_authenticate(user=user)

    # 2. Test Backup Endpoint
    print("\n[TEST] Endpoint de Backup (/api/maintenance/backup/)")
    try:
        response = client.get('/api/maintenance/backup/')
        if response.status_code == 200:
            print("✅ Backup generado correctamente. Status: 200")
            # Verify content is roughly JSON (dumpdata output)
            content = response.content.decode('utf-8')
            if content.startswith('['):
                 print("✅ El contenido parece ser un JSON válido (dumpdata output).")
            else:
                 print(f"⚠️ El contenido no empieza con '['. Inicio: {content[:50]}")
        else:
            print(f"❌ Error al generar Backup. Status: {response.status_code}, Error: {response.data}")
    except Exception as e:
        print(f"❌ Excepción al probar Backup: {e}")

    # 3. Test Logs Endpoint
    print("\n[TEST] Endpoint de Logs (/api/maintenance/log/)")
    try:
        response = client.get('/api/maintenance/log/')
        if response.status_code == 200:
            print("✅ Logs leídos correctamente. Status: 200")
            print(f"   Tamaño del log: {len(response.data.get('log', ''))} caracteres")
        else:
           print(f"❌ Error al leer Logs. Status: {response.status_code}, Error: {response.data}")
    except Exception as e:
        print(f"❌ Excepción al probar Logs: {e}")

    # 4. Test User Maintenance (List and Delete)
    print("\n[TEST] Endpoint de Usuarios (/api/maintenance/users/)")
    
    # Create dummy user to delete
    dummy_user = User.objects.create_user(username="to_delete_user", password="password")
    dummy_id = dummy_user.id
    
    # List
    response = client.get('/api/maintenance/users/')
    if response.status_code == 200:
        print("✅ Lista de usuarios obtenida. Status: 200")
        users = response.data
        if any(u['id'] == dummy_id for u in users):
             print("✅ Usuario de prueba encontrado en la lista.")
        else:
             print("❌ Usuario de prueba NO encontrado en la lista.")
    else:
        print(f"❌ Error al listar usuarios. Status: {response.status_code}")

    # Delete
    print(f"   Intentando eliminar usuario ID: {dummy_id}")
    response = client.delete('/api/maintenance/users/', {'user_ids': [dummy_id]}, format='json')
    if response.status_code == 200:
        print("✅ Usuario eliminado correctamente. Status: 200")
        if not User.objects.filter(id=dummy_id).exists():
            print("✅ Verificación en DB: El usuario ya no existe.")
        else:
             print("❌ Verificación en DB: El usuario AÚN EXISTE.")
    else:
        print(f"❌ Error al eliminar usuario. Status: {response.status_code}, Error: {response.data}")

    # 5. Restore (Mock)
    # We won't proceed with a real restore to avoid messing up the DB, but we verify endpoint existence/auth
    print("\n[TEST] Endpoint de Restore (/api/maintenance/restore/) - Chequeo de acceso")
    response = client.post('/api/maintenance/restore/') # No file
    if response.status_code == 400: # Bad Request expected (missing file)
         print("✅ Endpoint responde (400 Bad Request esperado por falta de archivo).")
    elif response.status_code == 401 or response.status_code == 403:
         print(f"❌ Error de permisos en Restore. Status: {response.status_code}")
    else:
         print(f"⚠️ Respuesta inesperada en Restore: {response.status_code}")

    # Cleanup
    if User.objects.filter(username=username).exists():
        # Do not delete if it was existing, but here we created it or got it. 
        # If we created it, we should verify cleanup. 
        # For simplicity, let's leave it or delete if we created it.
        pass

if __name__ == '__main__':
    try:
        verify_maintenance()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
